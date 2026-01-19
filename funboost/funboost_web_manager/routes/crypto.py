# -*- coding: utf-8 -*-
"""
加密相关路由模块

提供公钥分发 API，供前端获取用于密码加密的公钥。
"""

import logging
from flask import Blueprint, jsonify, request, make_response
from flask_login import login_required

from funboost.funboost_web_manager.services.encryption_service import get_encryption_service
from funboost.funboost_web_manager.routes.utils import require_permission

logger = logging.getLogger(__name__)

crypto_bp = Blueprint("crypto", __name__)


@crypto_bp.route("/api/public_key", methods=["GET"])
def get_public_key():
    """获取 RSA 公钥
    
    此端点无需认证，允许未登录用户获取公钥用于密码加密。
    
    Returns:
        JSON: {
            "public_key": str,  # PEM 格式公钥
            "key_id": str       # 密钥标识符
        }
        
    Headers:
        Cache-Control: public, max-age=3600
    """
    try:
        # 记录审计日志
        ip_address = request.remote_addr or "unknown"
        user_agent = request.headers.get("User-Agent", "")
        logger.info(f"公钥请求 - IP: {ip_address}, UA: {user_agent[:100]}")
        
        # 获取加密服务实例
        encryption_service = get_encryption_service()
        
        # 获取公钥
        key_data = encryption_service.get_public_key()
        
        # 创建响应
        response = make_response(jsonify(key_data))
        
        # 添加缓存头 - 允许客户端缓存 1 小时
        response.headers["Cache-Control"] = "public, max-age=3600"
        
        return response
        
    except Exception as e:
        logger.error(f"获取公钥失败: {e}")
        return jsonify({"error": "获取公钥失败"}), 500


@crypto_bp.route("/api/key_info", methods=["GET"])
@login_required
@require_permission("audit:read")
def get_key_info():
    """获取密钥信息（仅用于调试）
    
    此端点返回密钥的元信息，不包含实际密钥内容。
    需要 audit:read 权限。
    
    Returns:
        JSON: 密钥信息
    """
    try:
        encryption_service = get_encryption_service()
        return jsonify(encryption_service.get_key_info())
    except Exception as e:
        logger.error(f"获取密钥信息失败: {e}")
        return jsonify({"error": "获取密钥信息失败"}), 500
