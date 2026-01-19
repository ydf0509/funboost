# -*- coding: utf-8 -*-
"""
配置管理工具

提供配置文件读写、环境变量支持和配置验证功能
"""

import os
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field

from .platform import Platform


@dataclass
class ConfigValidationError:
    """配置验证错误"""
    key: str
    message: str
    value: Any = None
    suggestion: Optional[str] = None


@dataclass
class ConfigSchema:
    """配置项模式定义"""
    key: str
    type: type
    required: bool = False
    default: Any = None
    description: str = ""
    env_var: Optional[str] = None
    validator: Optional[callable] = None
    choices: Optional[List[Any]] = None


class ConfigManager:
    """配置管理器"""
    
    # 默认配置文件路径
    DEFAULT_CONFIG_FILE = "admin_config.json"
    DEFAULT_ENV_FILE = ".env"
    
    # 配置模式定义
    CONFIG_SCHEMAS: Dict[str, List[ConfigSchema]] = {
        "admin_config": [
            ConfigSchema(
                key="admin_user.username",
                type=str,
                required=True,
                description="管理员用户名",
                validator=lambda x: len(x) >= 3,
            ),
            ConfigSchema(
                key="admin_user.email",
                type=str,
                required=True,
                description="管理员邮箱",
                validator=lambda x: "@" in x and "." in x,
            ),
            ConfigSchema(
                key="admin_user.password",
                type=str,
                required=True,
                description="管理员密码",
                validator=lambda x: len(x) >= 8,
            ),
            ConfigSchema(
                key="admin_user.force_password_change",
                type=bool,
                required=False,
                default=True,
                description="首次登录是否强制修改密码",
            ),
            ConfigSchema(
                key="remove_default_users",
                type=bool,
                required=False,
                default=False,
                description="是否删除默认用户",
            ),
            ConfigSchema(
                key="default_users_to_remove",
                type=list,
                required=False,
                default=[],
                description="要删除的默认用户列表",
            ),
            ConfigSchema(
                key="frontend_url",
                type=str,
                required=False,
                default="",
                description="前端 URL",
            ),
        ],
        "env": [
            ConfigSchema(
                key="FUNBOOST_WEB_HOST",
                type=str,
                required=False,
                default="0.0.0.0",
                description="监听地址",
                env_var="FUNBOOST_WEB_HOST",
            ),
            ConfigSchema(
                key="FUNBOOST_WEB_PORT",
                type=int,
                required=False,
                default=27018,
                description="监听端口",
                env_var="FUNBOOST_WEB_PORT",
                validator=lambda x: 1 <= x <= 65535,
            ),
            ConfigSchema(
                key="FUNBOOST_DEBUG",
                type=bool,
                required=False,
                default=False,
                description="调试模式",
                env_var="FUNBOOST_DEBUG",
            ),
            ConfigSchema(
                key="FUNBOOST_SECRET_KEY",
                type=str,
                required=True,
                description="Flask 密钥",
                env_var="FUNBOOST_SECRET_KEY",
                validator=lambda x: len(x) >= 16,
            ),
            ConfigSchema(
                key="FUNBOOST_SESSION_SECURE",
                type=bool,
                required=False,
                default=False,
                description="Session Cookie 是否仅通过 HTTPS 传输",
                env_var="FUNBOOST_SESSION_SECURE",
            ),
            ConfigSchema(
                key="FUNBOOST_SESSION_SAMESITE",
                type=str,
                required=False,
                default="Lax",
                description="Session Cookie SameSite 策略",
                env_var="FUNBOOST_SESSION_SAMESITE",
                choices=["Strict", "Lax", "None"],
            ),
            ConfigSchema(
                key="FUNBOOST_CORS_ORIGINS",
                type=str,
                required=False,
                default="",
                description="允许的跨域来源",
                env_var="FUNBOOST_CORS_ORIGINS",
            ),
            ConfigSchema(
                key="FUNBOOST_FRONTEND_ENABLED",
                type=bool,
                required=False,
                default=True,
                description="是否启用前端服务",
                env_var="FUNBOOST_FRONTEND_ENABLED",
            ),
            ConfigSchema(
                key="FRONTEND_URL",
                type=str,
                required=False,
                default="",
                description="前端 URL",
                env_var="FRONTEND_URL",
            ),
        ],
    }
    
    def __init__(self, config_file: Optional[str] = None, env_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径（相对于项目根目录）
            env_file: 环境变量文件路径（相对于项目根目录）
        """
        self.project_root = Platform.PROJECT_ROOT
        self.config_file = self.project_root / (config_file or self.DEFAULT_CONFIG_FILE)
        self.env_file = self.project_root / (env_file or self.DEFAULT_ENV_FILE)
        
        # 缓存
        self._config_cache: Optional[Dict] = None
        self._env_cache: Optional[Dict] = None
    
    # ==================== 配置文件操作 ====================
    
    def read_config(self, reload: bool = False) -> Dict[str, Any]:
        """
        读取配置文件
        
        Args:
            reload: 是否强制重新加载
        
        Returns:
            配置字典
        """
        if self._config_cache is not None and not reload:
            return self._config_cache
        
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config_cache = json.load(f)
                return self._config_cache
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")
        except Exception as e:
            raise IOError(f"读取配置文件失败: {e}")
    
    def write_config(self, config: Dict[str, Any], merge: bool = True) -> bool:
        """
        写入配置文件
        
        Args:
            config: 配置字典
            merge: 是否与现有配置合并
        
        Returns:
            是否成功
        """
        try:
            if merge and self.config_file.exists():
                existing = self.read_config(reload=True)
                config = self._deep_merge(existing, config)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self._config_cache = config
            return True
        except Exception as e:
            raise IOError(f"写入配置文件失败: {e}")
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的嵌套键）
        
        Args:
            key: 配置键（如 "admin_user.username"）
            default: 默认值
        
        Returns:
            配置值
        """
        config = self.read_config()
        return self._get_nested_value(config, key, default)
    
    def set_config_value(self, key: str, value: Any) -> bool:
        """
        设置配置值（支持点号分隔的嵌套键）
        
        Args:
            key: 配置键（如 "admin_user.username"）
            value: 配置值
        
        Returns:
            是否成功
        """
        config = self.read_config()
        self._set_nested_value(config, key, value)
        return self.write_config(config, merge=False)
    
    def delete_config_value(self, key: str) -> bool:
        """
        删除配置值
        
        Args:
            key: 配置键
        
        Returns:
            是否成功
        """
        config = self.read_config()
        if self._delete_nested_value(config, key):
            return self.write_config(config, merge=False)
        return False
    
    def config_exists(self) -> bool:
        """检查配置文件是否存在"""
        return self.config_file.exists()
    
    def create_config_from_example(self) -> bool:
        """从示例文件创建配置文件"""
        example_file = self.project_root / "admin_config.example.json"
        if not example_file.exists():
            return False
        
        if self.config_file.exists():
            return False
        
        try:
            import shutil
            shutil.copy(example_file, self.config_file)
            return True
        except Exception:
            return False
    
    # ==================== 环境变量操作 ====================
    
    def read_env(self, reload: bool = False) -> Dict[str, str]:
        """
        读取 .env 文件
        
        Args:
            reload: 是否强制重新加载
        
        Returns:
            环境变量字典
        """
        if self._env_cache is not None and not reload:
            return self._env_cache
        
        if not self.env_file.exists():
            return {}
        
        env_vars = {}
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释
                    if not line or line.startswith('#'):
                        continue
                    
                    # 解析 KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 移除引号
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        
                        env_vars[key] = value
            
            self._env_cache = env_vars
            return env_vars
        except Exception as e:
            raise IOError(f"读取 .env 文件失败: {e}")
    
    def write_env(self, env_vars: Dict[str, str], merge: bool = True) -> bool:
        """
        写入 .env 文件
        
        Args:
            env_vars: 环境变量字典
            merge: 是否与现有变量合并
        
        Returns:
            是否成功
        """
        try:
            # 读取现有内容（保留注释和格式）
            lines = []
            existing_keys = set()
            
            if merge and self.env_file.exists():
                with open(self.env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        original_line = line
                        line = line.strip()
                        
                        if not line or line.startswith('#'):
                            lines.append(original_line.rstrip('\n'))
                            continue
                        
                        if '=' in line:
                            key = line.split('=', 1)[0].strip()
                            if key in env_vars:
                                # 更新现有值
                                lines.append(f"{key}={env_vars[key]}")
                                existing_keys.add(key)
                            else:
                                lines.append(original_line.rstrip('\n'))
                        else:
                            lines.append(original_line.rstrip('\n'))
                
                # 添加新的变量
                for key, value in env_vars.items():
                    if key not in existing_keys:
                        lines.append(f"{key}={value}")
            else:
                # 直接写入
                for key, value in env_vars.items():
                    lines.append(f"{key}={value}")
            
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines) + '\n')
            
            self._env_cache = None  # 清除缓存
            return True
        except Exception as e:
            raise IOError(f"写入 .env 文件失败: {e}")
    
    def get_env_value(self, key: str, default: str = "") -> str:
        """
        获取环境变量值
        
        优先级: 系统环境变量 > .env 文件
        
        Args:
            key: 环境变量名
            default: 默认值
        
        Returns:
            环境变量值
        """
        # 先检查系统环境变量
        if key in os.environ:
            return os.environ[key]
        
        # 再检查 .env 文件
        env_vars = self.read_env()
        return env_vars.get(key, default)
    
    def set_env_value(self, key: str, value: str) -> bool:
        """
        设置环境变量值（写入 .env 文件）
        
        Args:
            key: 环境变量名
            value: 环境变量值
        
        Returns:
            是否成功
        """
        return self.write_env({key: value}, merge=True)
    
    def env_exists(self) -> bool:
        """检查 .env 文件是否存在"""
        return self.env_file.exists()
    
    def create_env_from_example(self) -> bool:
        """从示例文件创建 .env 文件"""
        example_file = self.project_root / ".env.example"
        if not example_file.exists():
            return False
        
        if self.env_file.exists():
            return False
        
        try:
            import shutil
            shutil.copy(example_file, self.env_file)
            return True
        except Exception:
            return False
    
    def load_env_to_system(self) -> int:
        """
        将 .env 文件中的变量加载到系统环境变量
        
        Returns:
            加载的变量数量
        """
        env_vars = self.read_env()
        count = 0
        for key, value in env_vars.items():
            if key not in os.environ:
                os.environ[key] = value
                count += 1
        return count
    
    # ==================== 配置验证 ====================
    
    def validate_config(self, schema_name: str = "admin_config") -> Tuple[bool, List[ConfigValidationError]]:
        """
        验证配置文件
        
        Args:
            schema_name: 模式名称
        
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        schemas = self.CONFIG_SCHEMAS.get(schema_name, [])
        
        if schema_name == "admin_config":
            config = self.read_config()
        elif schema_name == "env":
            config = self.read_env()
        else:
            return False, [ConfigValidationError("schema", f"未知的配置模式: {schema_name}")]
        
        for schema in schemas:
            value = self._get_nested_value(config, schema.key, None)
            
            # 检查必填项
            if schema.required and value is None:
                errors.append(ConfigValidationError(
                    key=schema.key,
                    message=f"缺少必填配置项",
                    suggestion=f"请设置 {schema.key}（{schema.description}）"
                ))
                continue
            
            # 如果值为空且非必填，跳过验证
            if value is None:
                continue
            
            # 类型转换和验证
            try:
                if schema.type == bool:
                    if isinstance(value, str):
                        value = value.lower() in ('true', '1', 'yes', 'on')
                elif schema.type == int:
                    value = int(value)
                elif schema.type == float:
                    value = float(value)
            except (ValueError, TypeError):
                errors.append(ConfigValidationError(
                    key=schema.key,
                    message=f"类型错误，期望 {schema.type.__name__}",
                    value=value
                ))
                continue
            
            # 检查选项
            if schema.choices and value not in schema.choices:
                errors.append(ConfigValidationError(
                    key=schema.key,
                    message=f"无效的值，可选值: {schema.choices}",
                    value=value
                ))
                continue
            
            # 自定义验证
            if schema.validator and not schema.validator(value):
                errors.append(ConfigValidationError(
                    key=schema.key,
                    message=f"验证失败",
                    value=value,
                    suggestion=schema.description
                ))
        
        return len(errors) == 0, errors
    
    def validate_all(self) -> Tuple[bool, Dict[str, List[ConfigValidationError]]]:
        """
        验证所有配置
        
        Returns:
            (是否全部有效, {模式名: 错误列表})
        """
        all_errors = {}
        all_valid = True
        
        for schema_name in self.CONFIG_SCHEMAS.keys():
            valid, errors = self.validate_config(schema_name)
            if not valid:
                all_valid = False
                all_errors[schema_name] = errors
        
        return all_valid, all_errors
    
    # ==================== 辅助方法 ====================
    
    def _get_nested_value(self, data: Dict, key: str, default: Any = None) -> Any:
        """获取嵌套字典的值"""
        keys = key.split('.')
        value = data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def _set_nested_value(self, data: Dict, key: str, value: Any) -> None:
        """设置嵌套字典的值"""
        keys = key.split('.')
        current = data
        
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def _delete_nested_value(self, data: Dict, key: str) -> bool:
        """删除嵌套字典的值"""
        keys = key.split('.')
        current = data
        
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                return False
            current = current[k]
        
        if keys[-1] in current:
            del current[keys[-1]]
            return True
        return False
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """深度合并字典"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_all_config_keys(self, schema_name: str = "admin_config") -> List[str]:
        """获取所有配置键"""
        schemas = self.CONFIG_SCHEMAS.get(schema_name, [])
        return [s.key for s in schemas]
    
    def get_config_schema(self, key: str, schema_name: str = "admin_config") -> Optional[ConfigSchema]:
        """获取配置项的模式定义"""
        schemas = self.CONFIG_SCHEMAS.get(schema_name, [])
        for schema in schemas:
            if schema.key == key:
                return schema
        return None
    
    def export_config(self, include_env: bool = True) -> Dict[str, Any]:
        """
        导出所有配置
        
        Args:
            include_env: 是否包含环境变量
        
        Returns:
            配置字典
        """
        result = {
            "config_file": str(self.config_file),
            "config": self.read_config() if self.config_exists() else {},
        }
        
        if include_env:
            result["env_file"] = str(self.env_file)
            result["env"] = self.read_env() if self.env_exists() else {}
        
        return result


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
