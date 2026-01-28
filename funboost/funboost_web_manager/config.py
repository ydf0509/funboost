# -*- coding: utf-8 -*-
"""
Web Manager 配置模块

支持通过环境变量配置所有运行时参数，便于 Docker 和 Kubernetes 部署。

环境变量列表：
- FUNBOOST_WEB_HOST: 监听地址，默认 0.0.0.0
- FUNBOOST_WEB_PORT: 监听端口，默认 27018
- FUNBOOST_CORS_ORIGINS: 允许的跨域来源，逗号分隔，默认空（同源）
- FUNBOOST_SESSION_SECURE: Session Cookie 是否仅 HTTPS，默认 false
- FUNBOOST_SESSION_SAMESITE: Session Cookie SameSite 策略，默认 Lax
- FUNBOOST_SECRET_KEY: Flask 密钥，默认 mtfy54321
- FUNBOOST_FRONTEND_ENABLED: 是否启用前端服务，默认 true
"""

import os
from typing import List, Optional


class WebManagerConfig:
    """Web Manager 配置类，支持环境变量覆盖"""
    
    # ----- 服务器配置 -----
    
    @property
    def HOST(self) -> str:
        """监听地址"""
        return os.environ.get('FUNBOOST_WEB_HOST', '0.0.0.0')
    
    @property
    def PORT(self) -> int:
        """监听端口"""
        return int(os.environ.get('FUNBOOST_WEB_PORT', '27018'))
    
    # ----- CORS 配置 -----
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """
        允许的跨域来源列表
        
        环境变量格式：逗号分隔的 URL 列表
        例如：http://localhost:3000,http://127.0.0.1:3000
        
        如果未设置，返回空列表（仅允许同源请求）
        """
        origins_str = os.environ.get('FUNBOOST_CORS_ORIGINS', '')
        if not origins_str:
            return []
        return [origin.strip() for origin in origins_str.split(',') if origin.strip()]
    
    @property
    def CORS_ORIGINS_WITH_DEFAULTS(self) -> List[str]:
        """
        允许的跨域来源列表（包含开发环境默认值）
        
        如果环境变量未设置，返回开发环境常用的 localhost 地址
        """
        origins = self.CORS_ORIGINS
        if not origins:
            # 开发环境默认值
            return [
                'http://localhost:3000',
                'http://127.0.0.1:3000',
            ]
        return origins
    
    # ----- Session 配置 -----
    
    @property
    def SESSION_COOKIE_SECURE(self) -> bool:
        """Session Cookie 是否仅通过 HTTPS 传输"""
        return os.environ.get('FUNBOOST_SESSION_SECURE', 'false').lower() == 'true'
    
    @property
    def SESSION_COOKIE_SAMESITE(self) -> str:
        """
        Session Cookie SameSite 策略
        
        可选值：Strict, Lax, None
        - Strict: 最严格，跨站请求不发送 Cookie
        - Lax: 默认值，导航到目标网站的 GET 请求会发送 Cookie
        - None: 跨站请求也发送 Cookie（需要 Secure=True）
        """
        return os.environ.get('FUNBOOST_SESSION_SAMESITE', 'Lax')
    
    # ----- 安全配置 -----
    
    @property
    def SECRET_KEY(self) -> str:
        """Flask 密钥"""
        return os.environ.get('FUNBOOST_SECRET_KEY', 'mtfy54321')
    
    # ----- 前端配置 -----
    
    @property
    def FRONTEND_ENABLED(self) -> bool:
        """是否启用前端服务"""
        return os.environ.get('FUNBOOST_FRONTEND_ENABLED', 'true').lower() == 'true'
    
    # ----- 调试配置 -----
    
    @property
    def DEBUG(self) -> bool:
        """是否开启调试模式"""
        return os.environ.get('FUNBOOST_DEBUG', 'false').lower() == 'true'


# 全局配置实例
config = WebManagerConfig()
