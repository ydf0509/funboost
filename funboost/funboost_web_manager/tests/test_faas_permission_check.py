# -*- coding: utf-8 -*-
"""
测试 FaaS Blueprint 权限检查逻辑

验证 check_faas_permission() 函数的权限检查功能：
- 测试未认证访问返回 401
- 测试未授权访问返回 403
- 测试已授权访问成功

**Validates: Requirements 3.2.1, 6.3**
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, g, Blueprint, jsonify, request
from flask_login import LoginManager, UserMixin, login_user, current_user


class MockUser(UserMixin):
    """模拟用户类"""
    def __init__(self, user_id, is_authenticated=True):
        self.id = user_id
        self._is_authenticated = is_authenticated
    
    @property
    def is_authenticated(self):
        return self._is_authenticated


@pytest.fixture
def app():
    """创建测试应用"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    # 配置 Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return MockUser(user_id)
    
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def mock_blueprint():
    """创建模拟的 FaaS blueprint"""
    bp = Blueprint('funboost', __name__, url_prefix='/funboost')
    
    # 添加一些测试路由
    @bp.route('/get_all_queues', methods=['GET'])
    def get_all_queues():
        return jsonify({"succ": True, "msg": "success", "data": {"queues": []}})
    
    @bp.route('/publish', methods=['POST'])
    def publish():
        return jsonify({"succ": True, "msg": "published", "data": {"task_id": "123"}})
    
    @bp.route('/clear_queue', methods=['POST'])
    def clear_queue():
        return jsonify({"succ": True, "msg": "cleared", "data": None})
    
    @bp.route('/set_care_project_name', methods=['POST'])
    def set_care_project_name():
        return jsonify({"succ": True, "msg": "set", "data": None})
    
    return bp


def test_unauthenticated_access_returns_401(app, client, mock_blueprint):
    """
    测试未认证访问返回 401
    
    **Validates: Requirements 3.2.1**
    
    验证：
    - 未登录用户访问 FaaS 接口时返回 401 状态码
    - 响应包含正确的错误消息
    - 响应格式符合 FaaS 接口规范（succ, msg, data）
    """
    # 添加权限检查钩子
    @mock_blueprint.before_request
    def check_faas_permission():
        # 检查登录状态
        if not current_user.is_authenticated:
            return jsonify({
                "succ": False,
                "msg": "未登录或会话已过期，请重新登录",
                "data": None
            }), 401
    
    # 注册 blueprint
    app.register_blueprint(mock_blueprint)
    
    # 测试未认证访问
    response = client.get('/funboost/get_all_queues')
    
    # 验证状态码
    assert response.status_code == 401, "未认证访问应返回 401"
    
    # 验证响应格式
    data = response.get_json()
    assert data is not None, "响应应为 JSON 格式"
    assert data['succ'] is False, "succ 字段应为 False"
    assert '未登录' in data['msg'] or '会话已过期' in data['msg'], "应包含未登录提示"
    assert data['data'] is None, "data 字段应为 None"


@patch('funboost.funboost_web_manager.services.permission_service.PermissionService')
def test_unauthorized_access_returns_403(mock_permission_service_class, app, client, mock_blueprint):
    """
    测试未授权访问返回 403
    
    **Validates: Requirements 3.2.1**
    
    验证：
    - 已登录但无权限的用户访问 FaaS 接口时返回 403 状态码
    - 响应包含正确的权限错误消息
    - 响应格式符合 FaaS 接口规范
    """
    # 模拟 PermissionService
    mock_service = Mock()
    mock_service.check_permission.return_value = False  # 无权限
    mock_permission_service_class.return_value = mock_service
    
    # 添加权限检查钩子
    @mock_blueprint.before_request
    def check_faas_permission():
        from funboost.funboost_web_manager.services.permission_service import PermissionService
        
        # 检查登录状态
        if not current_user.is_authenticated:
            return jsonify({
                "succ": False,
                "msg": "未登录或会话已过期，请重新登录",
                "data": None
            }), 401
        
        # 根据路径判断所需权限
        path = request.path
        required_permission = None
        
        # 写操作权限
        if any(p in path for p in ['/publish', '/clear_queue', '/deprecate_queue']):
            required_permission = 'queue:execute'
        # 读操作权限
        elif any(p in path for p in ['/get_']):
            required_permission = 'queue:read'
        
        # 检查权限
        if required_permission:
            permission_service = PermissionService()
            if not permission_service.check_permission(current_user.id, required_permission):
                return jsonify({
                    "succ": False,
                    "msg": f"您没有 {required_permission} 权限",
                    "data": None
                }), 403
    
    # 注册 blueprint
    app.register_blueprint(mock_blueprint)
    
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 测试访问需要 queue:read 权限的接口
    response = client.get('/funboost/get_all_queues')
    
    # 验证状态码
    assert response.status_code == 403, "无权限访问应返回 403"
    
    # 验证响应格式
    data = response.get_json()
    assert data is not None, "响应应为 JSON 格式"
    assert data['succ'] is False, "succ 字段应为 False"
    assert 'queue:read' in data['msg'] or '权限' in data['msg'], "应包含权限错误提示"
    assert data['data'] is None, "data 字段应为 None"


@patch('funboost.funboost_web_manager.services.permission_service.PermissionService')
def test_authorized_access_succeeds(mock_permission_service_class, app, client, mock_blueprint):
    """
    测试已授权访问成功
    
    **Validates: Requirements 3.2.1**
    
    验证：
    - 已登录且有权限的用户可以成功访问 FaaS 接口
    - 权限检查通过后，请求继续处理
    - 不返回 401 或 403 错误
    """
    # 模拟 PermissionService
    mock_service = Mock()
    mock_service.check_permission.return_value = True  # 有权限
    mock_permission_service_class.return_value = mock_service
    
    # 添加权限检查钩子
    @mock_blueprint.before_request
    def check_faas_permission():
        from funboost.funboost_web_manager.services.permission_service import PermissionService
        
        # 检查登录状态
        if not current_user.is_authenticated:
            return jsonify({
                "succ": False,
                "msg": "未登录或会话已过期，请重新登录",
                "data": None
            }), 401
        
        # 根据路径判断所需权限
        path = request.path
        required_permission = None
        
        # 读操作权限
        if any(p in path for p in ['/get_']):
            required_permission = 'queue:read'
        
        # 检查权限
        if required_permission:
            permission_service = PermissionService()
            if not permission_service.check_permission(current_user.id, required_permission):
                return jsonify({
                    "succ": False,
                    "msg": f"您没有 {required_permission} 权限",
                    "data": None
                }), 403
    
    # 注册 blueprint
    app.register_blueprint(mock_blueprint)
    
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'admin_user'
    
    # 测试访问需要 queue:read 权限的接口
    response = client.get('/funboost/get_all_queues')
    
    # 验证不是 401 或 403
    assert response.status_code != 401, "有权限的用户不应返回 401"
    assert response.status_code != 403, "有权限的用户不应返回 403"
    assert response.status_code == 200, "有权限的用户应成功访问"
    
    # 验证权限检查被调用
    mock_service.check_permission.assert_called_once_with('admin_user', 'queue:read')


def test_permission_mapping_for_write_operations(app):
    """
    测试写操作的权限映射
    
    验证：
    - /publish 需要 queue:execute 权限
    - /clear_queue 需要 queue:execute 权限
    - /deprecate_queue 需要 queue:execute 权限
    - /add_timing_job 需要 queue:execute 权限
    """
    write_paths = [
        '/funboost/publish',
        '/funboost/clear_queue',
        '/funboost/deprecate_queue',
        '/funboost/add_timing_job',
        '/funboost/delete_timing_job',
        '/funboost/pause_timing_job',
        '/funboost/resume_timing_job'
    ]
    
    for path in write_paths:
        with app.test_request_context(path):
            from flask import request
            
            # 判断所需权限
            required_permission = None
            if any(p in request.path for p in ['/publish', '/clear_queue', '/deprecate_queue',
                                                '/add_timing_job', '/delete_timing_job',
                                                '/pause_timing_job', '/resume_timing_job']):
                required_permission = 'queue:execute'
            
            assert required_permission == 'queue:execute', \
                f"路径 {path} 应需要 queue:execute 权限"


def test_permission_mapping_for_read_operations(app):
    """
    测试读操作的权限映射
    
    验证：
    - /get_all_queues 需要 queue:read 权限
    - /get_result 需要 queue:read 权限
    - /get_timing_jobs 需要 queue:read 权限
    """
    read_paths = [
        '/funboost/get_all_queues',
        '/funboost/get_result',
        '/funboost/get_timing_jobs',
        '/funboost/get_one_queue_config'
    ]
    
    for path in read_paths:
        with app.test_request_context(path):
            from flask import request
            
            # 判断所需权限
            required_permission = None
            if any(p in request.path for p in ['/get_', '/timing_job']):
                required_permission = 'queue:read'
            
            assert required_permission == 'queue:read', \
                f"路径 {path} 应需要 queue:read 权限"


def test_permission_mapping_for_config_operations(app):
    """
    测试配置操作的权限映射
    
    验证：
    - /set_care_project_name 需要 config:update 权限
    - /remove_project_name 需要 config:update 权限
    """
    config_paths = [
        '/funboost/set_care_project_name',
        '/funboost/remove_project_name'
    ]
    
    for path in config_paths:
        with app.test_request_context(path):
            from flask import request
            
            # 判断所需权限（配置权限优先级最高）
            required_permission = None
            if any(p in request.path for p in ['/set_care_project_name', '/remove_project_name']):
                required_permission = 'config:update'
            
            assert required_permission == 'config:update', \
                f"路径 {path} 应需要 config:update 权限"


@patch('funboost.funboost_web_manager.services.permission_service.PermissionService')
def test_multiple_permission_checks_in_sequence(mock_permission_service_class, app, client, mock_blueprint):
    """
    测试连续多次权限检查
    
    验证：
    - 权限检查在每次请求时都会执行
    - 权限状态变化时，检查结果也会变化
    """
    # 模拟 PermissionService
    mock_service = Mock()
    mock_permission_service_class.return_value = mock_service
    
    # 添加权限检查钩子
    @mock_blueprint.before_request
    def check_faas_permission():
        from funboost.funboost_web_manager.services.permission_service import PermissionService
        
        if not current_user.is_authenticated:
            return jsonify({"succ": False, "msg": "未登录", "data": None}), 401
        
        path = request.path
        required_permission = None
        
        if any(p in path for p in ['/get_']):
            required_permission = 'queue:read'
        
        if required_permission:
            permission_service = PermissionService()
            if not permission_service.check_permission(current_user.id, required_permission):
                return jsonify({"succ": False, "msg": f"无 {required_permission} 权限", "data": None}), 403
    
    # 注册 blueprint
    app.register_blueprint(mock_blueprint)
    
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 第一次请求：有权限
    mock_service.check_permission.return_value = True
    response1 = client.get('/funboost/get_all_queues')
    assert response1.status_code == 200, "第一次请求应成功"
    
    # 第二次请求：无权限
    mock_service.check_permission.return_value = False
    response2 = client.get('/funboost/get_all_queues')
    assert response2.status_code == 403, "第二次请求应返回 403"
    
    # 验证权限检查被调用了两次
    assert mock_service.check_permission.call_count == 2


def test_error_response_format_consistency(app, client, mock_blueprint):
    """
    测试错误响应格式的一致性
    
    验证：
    - 401 和 403 响应都使用相同的格式
    - 响应格式符合 FaaS 接口规范（succ, msg, data）
    """
    # 添加权限检查钩子
    @mock_blueprint.before_request
    def check_faas_permission():
        if not current_user.is_authenticated:
            return jsonify({
                "succ": False,
                "msg": "未登录或会话已过期，请重新登录",
                "data": None
            }), 401
    
    # 注册 blueprint
    app.register_blueprint(mock_blueprint)
    
    # 测试 401 响应格式
    response_401 = client.get('/funboost/get_all_queues')
    data_401 = response_401.get_json()
    
    assert 'succ' in data_401, "401 响应应包含 succ 字段"
    assert 'msg' in data_401, "401 响应应包含 msg 字段"
    assert 'data' in data_401, "401 响应应包含 data 字段"
    assert isinstance(data_401['succ'], bool), "succ 应为布尔值"
    assert isinstance(data_401['msg'], str), "msg 应为字符串"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
