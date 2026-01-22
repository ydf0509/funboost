# -*- coding: utf-8 -*-
"""
前端静态文件服务蓝图

服务 Next.js 构建的静态文件，支持 SPA 路由回退
"""

import os
import mimetypes
from flask import Blueprint, send_from_directory, current_app, abort

frontend_bp = Blueprint('frontend', __name__)

# 禁用严格斜杠模式，避免重定向循环
frontend_bp.strict_slashes = False

# 确保常见的 MIME 类型正确
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/json', '.json')
mimetypes.add_type('image/svg+xml', '.svg')
mimetypes.add_type('font/woff', '.woff')
mimetypes.add_type('font/woff2', '.woff2')


def get_frontend_dir() -> str:
    """获取前端静态文件目录"""
    static_folder = current_app.static_folder
    if static_folder is None:
        raise RuntimeError("Flask static_folder not configured")
    return os.path.join(static_folder, 'frontend')


def file_exists(directory: str, filename: str) -> bool:
    """检查文件是否存在"""
    filepath = os.path.join(directory, filename)
    return os.path.isfile(filepath)


def normalize_path(path: str) -> str:
    """
    规范化路径分隔符
    
    Flask/Werkzeug 的 send_from_directory 要求使用正斜杠作为路径分隔符，
    即使在 Windows 上也是如此。os.path.join 在 Windows 上会使用反斜杠，
    所以需要转换。
    """
    return path.replace('\\', '/')


@frontend_bp.route('/')
def serve_index():
    """服务首页"""
    frontend_dir = get_frontend_dir()
    
    # 检查前端是否已构建
    index_path = os.path.join(frontend_dir, 'index.html')
    if not os.path.isfile(index_path):
        return (
            '<h1>前端未构建</h1>'
            '<p>请先在 web-manager-frontend 目录执行 <code>npm run build</code></p>',
            503
        )
    
    return send_from_directory(frontend_dir, 'index.html')


@frontend_bp.route('/favicon.ico')
def serve_favicon():
    """服务 favicon"""
    frontend_dir = get_frontend_dir()
    
    # 优先从前端目录获取
    if file_exists(frontend_dir, 'favicon.ico'):
        return send_from_directory(frontend_dir, 'favicon.ico')
    
    # 回退到 images 目录
    images_dir = os.path.join(current_app.static_folder, 'images')
    if file_exists(images_dir, 'favicon.ico'):
        return send_from_directory(images_dir, 'favicon.ico')
    
    abort(404)


@frontend_bp.route('/_next/<path:filename>')
def serve_next_static(filename: str):
    """服务 Next.js 静态资源（_next 目录）"""
    frontend_dir = get_frontend_dir()
    next_dir = os.path.join(frontend_dir, '_next')
    
    if not os.path.isdir(next_dir):
        abort(404)
    
    filepath = os.path.join(next_dir, filename)
    if not os.path.isfile(filepath):
        abort(404)
    
    # 设置缓存头（静态资源可以长期缓存）
    # 规范化路径分隔符
    response = send_from_directory(next_dir, normalize_path(filename))
    
    # _next/static 目录下的文件包含 hash，可以长期缓存
    if filename.startswith('static/'):
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    else:
        response.headers['Cache-Control'] = 'public, max-age=3600'
    
    return response


@frontend_bp.route('/<path:path>')
def serve_frontend(path: str):
    """
    服务前端页面和静态文件
    
    处理逻辑：
    1. 排除 API 和 FAAS 路由（让其他蓝图处理）
    2. 尝试直接返回请求的文件
    3. 尝试添加 .html 后缀
    4. 尝试作为目录，返回 index.html
    5. 回退到首页（SPA 路由）
    """
    # 排除 FAAS 蓝图路由（兼容上游仓库）
    # 这些路由应该由其他蓝图处理，不应该被前端 catch-all 拦截
    if path.startswith('funboost/') or path.startswith('api/') or path.startswith('admin/'):
        # 返回 404，让 Flask 继续查找其他路由
        from flask import abort
        abort(404)
    
    frontend_dir = get_frontend_dir()
    
    # 检查前端是否已构建
    if not os.path.isdir(frontend_dir):
        return (
            '<h1>前端未构建</h1>'
            '<p>请先在 web-manager-frontend 目录执行 <code>npm run build</code></p>',
            503
        )
    
    # 1. 尝试直接返回请求的文件
    file_path = os.path.join(frontend_dir, path)
    if os.path.isfile(file_path):
        # 设置适当的缓存头
        # 规范化路径分隔符
        response = send_from_directory(frontend_dir, normalize_path(path))
        
        # HTML 文件不缓存，其他静态资源缓存
        if path.endswith('.html'):
            response.headers['Cache-Control'] = 'no-cache'
        else:
            response.headers['Cache-Control'] = 'public, max-age=3600'
        
        return response
    
    # 2. 尝试添加 .html 后缀
    html_path = f"{path}.html"
    if file_exists(frontend_dir, html_path):
        response = send_from_directory(frontend_dir, normalize_path(html_path))
        response.headers['Cache-Control'] = 'no-cache'
        return response
    
    # 3. 尝试作为目录，返回 index.html
    # 处理带尾部斜杠的路径
    clean_path = path.rstrip('/')
    index_path = os.path.join(clean_path, 'index.html')
    if file_exists(frontend_dir, index_path):
        # 规范化路径分隔符（Flask/Werkzeug 要求使用正斜杠）
        response = send_from_directory(frontend_dir, normalize_path(index_path))
        response.headers['Cache-Control'] = 'no-cache'
        return response
    
    # 4. SPA 回退：返回首页
    index_file = os.path.join(frontend_dir, 'index.html')
    if os.path.isfile(index_file):
        response = send_from_directory(frontend_dir, 'index.html')
        response.headers['Cache-Control'] = 'no-cache'
        return response
    
    abort(404)
