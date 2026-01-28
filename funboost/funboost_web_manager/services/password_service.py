# -*- coding: utf-8 -*-
"""
密码服务模块

提供密码哈希、验证和强度检查功能。
"""

import bcrypt
import re
from typing import Tuple, List


class PasswordService:
    """密码哈希和验证服务"""
    
    # 密码强度要求
    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        使用 bcrypt 哈希密码
        
        Args:
            password: 明文密码
            
        Returns:
            str: bcrypt 哈希后的密码
        """
        if not password:
            raise ValueError("密码不能为空")
            
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        验证密码，支持 bcrypt 哈希和明文兼容
        
        Args:
            password: 明文密码
            hashed: 存储的密码（可能是哈希或明文）
            
        Returns:
            bool: 密码是否匹配
        """
        if not password or not hashed:
            return False
            
        # 检查是否是 bcrypt 哈希（以 $2b$ 或 $2a$ 开头）
        if hashed.startswith('$2b$') or hashed.startswith('$2a$'):
            try:
                return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
            except (ValueError, TypeError):
                return False
        
        # 兼容旧的明文密码
        return password == hashed
    
    @staticmethod
    def is_hashed(password: str) -> bool:
        """
        检查密码是否已经是哈希格式
        
        Args:
            password: 密码字符串
            
        Returns:
            bool: 是否为哈希格式
        """
        if not password:
            return False
        return password.startswith('$2b$') or password.startswith('$2a$')
    
    @classmethod
    def validate_strength(cls, password: str) -> Tuple[bool, List[str]]:
        """
        验证密码强度，返回 (是否通过, 错误列表)
        
        Args:
            password: 待验证的密码
            
        Returns:
            Tuple[bool, List[str]]: (是否通过验证, 错误信息列表)
        """
        if not password:
            return False, ["密码不能为空"]
            
        errors = []
        
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"密码长度至少 {cls.MIN_LENGTH} 个字符")
        
        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("密码必须包含至少一个大写字母")
        
        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("密码必须包含至少一个小写字母")
        
        if cls.REQUIRE_DIGIT and not re.search(r'\d', password):
            errors.append("密码必须包含至少一个数字")
        
        if cls.REQUIRE_SPECIAL and not any(c in cls.SPECIAL_CHARS for c in password):
            errors.append(f"密码必须包含至少一个特殊字符 ({cls.SPECIAL_CHARS})")
        
        return len(errors) == 0, errors