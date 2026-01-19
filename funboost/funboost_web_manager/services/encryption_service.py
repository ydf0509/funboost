# -*- coding: utf-8 -*-
"""
RSA 加密服务模块

提供前端密码加密传输的后端支持：
- RSA 密钥对生成和管理
- 公钥分发
- 加密密码解密
- 密钥轮换
"""

import base64
import hashlib
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

logger = logging.getLogger(__name__)


class DecryptionError(Exception):
    """解密失败异常"""
    pass


class KeyNotFoundError(Exception):
    """密钥未找到异常"""
    pass


@dataclass
class KeyPair:
    """RSA 密钥对"""
    public_key_pem: str
    private_key_pem: str
    key_id: str
    created_at: datetime = field(default_factory=datetime.now)
    active: bool = True


class EncryptionService:
    """RSA 加密服务
    
    提供 RSA 非对称加密功能，用于前端密码加密传输。
    支持密钥轮换，保留旧密钥用于解密过渡期消息。
    """

    KEY_SIZE: int = 2048  # RSA 密钥长度
    MAX_OLD_KEYS: int = 3  # 保留的旧密钥数量

    def __init__(self, key_storage_path: Optional[str] = None):
        """初始化加密服务

        Args:
            key_storage_path: 密钥存储路径，None 则仅内存存储
        """
        self._key_storage_path = key_storage_path
        self._current_key: Optional[KeyPair] = None
        self._old_keys: Dict[str, KeyPair] = {}  # key_id -> KeyPair
        self._initialize_keys()

    def _initialize_keys(self) -> None:
        """初始化密钥对"""
        loaded = False
        
        # 尝试从文件加载
        if self._key_storage_path and os.path.exists(self._key_storage_path):
            try:
                loaded = self._load_keys_from_file()
            except Exception as e:
                logger.warning(f"加载密钥文件失败，将生成新密钥: {e}")
        
        # 如果没有加载成功，生成新密钥
        if not loaded or self._current_key is None:
            self._generate_new_key_pair()
            if self._key_storage_path:
                self._save_keys_to_file()

    def _generate_key_id(self) -> str:
        """生成密钥标识符"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"key_{timestamp}_{unique_id}"

    def _generate_new_key_pair(self) -> KeyPair:
        """生成新的 RSA 密钥对"""
        # 生成私钥
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.KEY_SIZE,
            backend=default_backend()
        )
        
        # 序列化私钥为 PEM 格式
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        # 获取公钥并序列化
        public_key = private_key.public_key()
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        # 创建密钥对对象
        key_pair = KeyPair(
            public_key_pem=public_key_pem,
            private_key_pem=private_key_pem,
            key_id=self._generate_key_id(),
            created_at=datetime.now(),
            active=True
        )
        
        self._current_key = key_pair
        logger.info(f"生成新密钥对: {key_pair.key_id}")
        return key_pair


    def _load_keys_from_file(self) -> bool:
        """从文件加载密钥"""
        if not self._key_storage_path or not os.path.exists(self._key_storage_path):
            return False
        
        try:
            with open(self._key_storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            current_key_id = data.get('current_key_id')
            keys_data = data.get('keys', {})
            
            for key_id, key_info in keys_data.items():
                key_pair = KeyPair(
                    public_key_pem=key_info['public_key_pem'],
                    private_key_pem=key_info['private_key_pem'],
                    key_id=key_id,
                    created_at=datetime.fromisoformat(key_info['created_at']),
                    active=key_info.get('active', False)
                )
                
                if key_id == current_key_id:
                    self._current_key = key_pair
                else:
                    self._old_keys[key_id] = key_pair
            
            logger.info(f"从文件加载密钥成功，当前密钥: {current_key_id}")
            return self._current_key is not None
            
        except Exception as e:
            logger.error(f"加载密钥文件失败: {e}")
            return False

    def _save_keys_to_file(self) -> None:
        """保存密钥到文件"""
        if not self._key_storage_path:
            return
        
        try:
            keys_data = {}
            
            # 保存当前密钥
            if self._current_key:
                keys_data[self._current_key.key_id] = {
                    'public_key_pem': self._current_key.public_key_pem,
                    'private_key_pem': self._current_key.private_key_pem,
                    'created_at': self._current_key.created_at.isoformat(),
                    'active': True
                }
            
            # 保存旧密钥
            for key_id, key_pair in self._old_keys.items():
                keys_data[key_id] = {
                    'public_key_pem': key_pair.public_key_pem,
                    'private_key_pem': key_pair.private_key_pem,
                    'created_at': key_pair.created_at.isoformat(),
                    'active': False
                }
            
            data = {
                'current_key_id': self._current_key.key_id if self._current_key else None,
                'keys': keys_data
            }
            
            # 确保目录存在
            os.makedirs(os.path.dirname(self._key_storage_path), exist_ok=True)
            
            with open(self._key_storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"密钥保存到文件: {self._key_storage_path}")
            
        except Exception as e:
            logger.error(f"保存密钥文件失败: {e}")

    def get_public_key(self) -> Dict[str, str]:
        """获取当前公钥

        Returns:
            {"public_key": str, "key_id": str}
        """
        if not self._current_key:
            self._generate_new_key_pair()
        
        logger.debug(f"获取公钥: {self._current_key.key_id}")
        return {
            "public_key": self._current_key.public_key_pem,
            "key_id": self._current_key.key_id
        }

    def _get_private_key(self, key_id: Optional[str] = None):
        """获取私钥对象
        
        Args:
            key_id: 密钥标识符，None 则使用当前密钥
            
        Returns:
            RSA 私钥对象
            
        Raises:
            KeyNotFoundError: 密钥未找到
        """
        key_pair = None
        
        if key_id is None:
            key_pair = self._current_key
        elif self._current_key and self._current_key.key_id == key_id:
            key_pair = self._current_key
        elif key_id in self._old_keys:
            key_pair = self._old_keys[key_id]
        
        if not key_pair:
            raise KeyNotFoundError(f"密钥未找到: {key_id}")
        
        # 加载私钥
        private_key = serialization.load_pem_private_key(
            key_pair.private_key_pem.encode('utf-8'),
            password=None,
            backend=default_backend()
        )
        return private_key

    def decrypt_password(self, encrypted_data: str, key_id: Optional[str] = None) -> str:
        """解密密码

        Args:
            encrypted_data: Base64 编码的加密数据
            key_id: 密钥标识符（用于密钥轮换场景）

        Returns:
            解密后的明文密码

        Raises:
            DecryptionError: 解密失败
        """
        try:
            # Base64 解码
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # 获取私钥
            private_key = self._get_private_key(key_id)
            
            # 使用 RSA-OAEP 解密
            decrypted_bytes = private_key.decrypt(
                encrypted_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return decrypted_bytes.decode('utf-8')
            
        except KeyNotFoundError:
            logger.warning(f"解密失败: 密钥未找到 key_id={key_id}")
            raise DecryptionError("密钥不匹配或已过期")
        except Exception as e:
            logger.warning(f"解密失败: {type(e).__name__}")
            raise DecryptionError("解密失败，数据格式无效")


    def is_encrypted_password(self, password_data: Any) -> bool:
        """检测密码是否为加密格式

        Args:
            password_data: 密码数据（可能是字符串或字典）

        Returns:
            True 如果是加密格式
        """
        if isinstance(password_data, dict):
            return password_data.get('encrypted', False) is True
        
        if isinstance(password_data, str):
            # 尝试解析 JSON
            try:
                data = json.loads(password_data)
                return isinstance(data, dict) and data.get('encrypted', False) is True
            except (json.JSONDecodeError, TypeError):
                return False
        
        return False

    def parse_encrypted_password(self, password_data: Any) -> Tuple[str, Optional[str]]:
        """解析加密密码格式

        Args:
            password_data: 加密密码数据

        Returns:
            (encrypted_data, key_id)
            
        Raises:
            ValueError: 格式无效
        """
        data = password_data
        
        # 如果是字符串，尝试解析 JSON
        if isinstance(password_data, str):
            try:
                data = json.loads(password_data)
            except (json.JSONDecodeError, TypeError):
                raise ValueError("无效的加密密码格式")
        
        if not isinstance(data, dict):
            raise ValueError("无效的加密密码格式")
        
        if not data.get('encrypted', False):
            raise ValueError("密码未标记为加密格式")
        
        encrypted_data = data.get('data')
        if not encrypted_data:
            raise ValueError("缺少加密数据")
        
        key_id = data.get('key_id')
        
        return encrypted_data, key_id

    def rotate_key(self) -> str:
        """轮换密钥

        Returns:
            新密钥的 key_id
        """
        # 将当前密钥移到旧密钥列表
        if self._current_key:
            self._current_key.active = False
            self._old_keys[self._current_key.key_id] = self._current_key
            logger.info(f"密钥 {self._current_key.key_id} 已标记为旧密钥")
        
        # 清理过多的旧密钥
        if len(self._old_keys) > self.MAX_OLD_KEYS:
            # 按创建时间排序，删除最旧的
            sorted_keys = sorted(
                self._old_keys.items(),
                key=lambda x: x[1].created_at
            )
            keys_to_remove = sorted_keys[:-self.MAX_OLD_KEYS]
            for key_id, _ in keys_to_remove:
                del self._old_keys[key_id]
                logger.info(f"删除过期密钥: {key_id}")
        
        # 生成新密钥
        new_key = self._generate_new_key_pair()
        
        # 保存到文件
        if self._key_storage_path:
            self._save_keys_to_file()
        
        logger.info(f"密钥轮换完成，新密钥: {new_key.key_id}")
        return new_key.key_id

    def extract_password(self, password_data: Any) -> str:
        """从请求数据中提取密码（支持加密和明文）
        
        这是一个便捷方法，用于在认证路由中提取密码。
        
        Args:
            password_data: 密码数据（可能是加密格式或明文）
            
        Returns:
            明文密码
            
        Raises:
            DecryptionError: 解密失败
        """
        if self.is_encrypted_password(password_data):
            encrypted_data, key_id = self.parse_encrypted_password(password_data)
            return self.decrypt_password(encrypted_data, key_id)
        
        # 明文密码
        if isinstance(password_data, str):
            return password_data
        
        raise ValueError("无效的密码格式")

    def get_key_info(self) -> Dict[str, Any]:
        """获取密钥信息（用于调试和监控）
        
        Returns:
            密钥信息字典
        """
        return {
            "current_key_id": self._current_key.key_id if self._current_key else None,
            "current_key_created_at": self._current_key.created_at.isoformat() if self._current_key else None,
            "old_keys_count": len(self._old_keys),
            "old_key_ids": list(self._old_keys.keys())
        }


# 全局单例实例
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service(key_storage_path: Optional[str] = None) -> EncryptionService:
    """获取加密服务单例
    
    Args:
        key_storage_path: 密钥存储路径（仅首次调用时有效）
        
    Returns:
        EncryptionService 实例
    """
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService(key_storage_path)
    return _encryption_service
