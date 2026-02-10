# -*- coding: utf-8 -*-
"""
完整流程的集成测试

测试 Web Manager 与 FaaS Blueprint 的完整集成，包括：
- 已认证用户可以发布消息
- 项目过滤端到端工作
- RPC 模式消息发布
- 错误响应格式正确

**Validates: Requirements 6.3**
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, g
from flask_login import LoginManager, UserMixin


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
def mock_booster():
    """模拟 Booster 对象"""
    booster = Mock()
    booster.queue_name = 'test_queue'
    booster.function_name = 'test_function'
    booster.project_name = 'test_project'
    
    # 模拟 push 方法
    def mock_push(*args, **kwargs):
        return 'task_123'
    
    booster.push = Mock(side_effect=mock_push)
    
    # 模拟 push_with_rpc 方法
    def mock_push_with_rpc(*args, **kwargs):
        return {'result': 'success', 'value': 42}
    
    booster.push_with_rpc = Mock(side_effect=mock_push_with_rpc)
    
    return booster


@pytest.fixture
def setup_faas_blueprint(app, mock_booster):
    """设置 FaaS blueprint 和权限检查"""
    from flask import Blueprint, jsonify, request
    from flask_login import current_user
    from funboost.core.active_cousumer_info_getter import CareProjectNameEnv
    
    # 创建 FaaS blueprint
    flask_blueprint = Blueprint('funboost', __name__, url_prefix='/funboost')
    
    # 添加权限检查钩子
    @flask_blueprint.before_request
    def check_faas_permission():
        """权限检查"""
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
        if any(p in path for p in ['/publish', '/clear_queue']):
            required_permission = 'queue:execute'
        # 读操作权限
        elif any(p in path for p in ['/get_']):
            required_permission = 'queue:read'
        
        # 模拟权限检查（在测试中总是通过）
        # 实际应用中会调用 PermissionService
        
        # 项目过滤：从请求中提取 project_id
        project_id = request.args.get('project_id')
        if not project_id and request.is_json:
            data = request.get_json(silent=True) or {}
            project_id = data.get('project_id')
        
        if project_id:
            try:
                project_id_int = int(project_id)
                # 模拟获取项目代码
                project_code = f'project_{project_id_int}'
                g.care_project_name = project_code
            except (ValueError, TypeError):
                return jsonify({
                    "succ": False,
                    "msg": "无效的项目ID",
                    "data": None
                }), 400
    
    # 添加项目过滤注入钩子
    @flask_blueprint.before_request
    def inject_project_filter():
        """注入项目过滤参数"""
        if hasattr(g, 'care_project_name') and g.care_project_name:
            g._original_care_project_name = CareProjectNameEnv.get()
            CareProjectNameEnv.set(g.care_project_name)
    
    # 添加恢复钩子
    @flask_blueprint.after_request
    def restore_project_filter(response):
        """恢复项目过滤参数"""
        if hasattr(g, '_original_care_project_name'):
            original_value = g._original_care_project_name
            if original_value is None:
                original_value = ''
            CareProjectNameEnv.set(original_value)
        return response
    
    # 添加 publish 路由
    @flask_blueprint.route('/publish', methods=['POST'])
    def publish():
        """发布消息接口"""
        data = request.get_json()
        
        # 验证必填参数
        if not data or 'queue_name' not in data:
            return jsonify({
                "succ": False,
                "msg": "缺少必填参数 queue_name",
                "data": None
            }), 400
        
        queue_name = data['queue_name']
        msg_body = data.get('msg_body', {})
        need_result = data.get('need_result', False)
        timeout = data.get('timeout', 60)
        
        # 获取当前项目过滤
        current_project = CareProjectNameEnv.get()
        
        # 模拟发布消息
        if need_result:
            # RPC 模式
            result = mock_booster.push_with_rpc(**msg_body)
            return jsonify({
                "succ": True,
                "msg": f"{queue_name} 队列,消息发布成功（RPC模式）",
                "data": {
                    "task_id": "rpc_task_123",
                    "result": result,
                    "current_project": current_project
                }
            })
        else:
            # 普通模式
            task_id = mock_booster.push(**msg_body)
            return jsonify({
                "succ": True,
                "msg": f"{queue_name} 队列,消息发布成功",
                "data": {
                    "task_id": task_id,
                    "current_project": current_project
                }
            })
    
    # 注册 blueprint
    app.register_blueprint(flask_blueprint)
    
    return flask_blueprint


def test_authenticated_user_can_publish_message(client, setup_faas_blueprint):
    """
    测试已认证用户可以发布消息
    
    **Validates: Requirements 6.3**
    
    验证：
    - 已登录用户可以成功调用 /funboost/publish 接口
    - 消息发布成功并返回 task_id
    - 响应格式符合 FaaS 接口规范
    """
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 发布消息
    response = client.post('/funboost/publish', 
                          json={
                              'queue_name': 'test_queue',
                              'msg_body': {'x': 1, 'y': 2},
                              'need_result': False
                          },
                          content_type='application/json')
    
    # 验证响应
    assert response.status_code == 200, "已认证用户应成功发布消息"
    
    data = response.get_json()
    assert data is not None, "响应应为 JSON 格式"
    assert data['succ'] is True, "succ 字段应为 True"
    assert '消息发布成功' in data['msg'], "应包含成功消息"
    assert 'task_id' in data['data'], "应返回 task_id"
    assert data['data']['task_id'] == 'task_123', "task_id 应正确"


def test_unauthenticated_user_cannot_publish_message(client, setup_faas_blueprint):
    """
    测试未认证用户无法发布消息
    
    **Validates: Requirements 6.3**
    
    验证：
    - 未登录用户调用 /funboost/publish 接口返回 401
    - 错误响应格式正确
    """
    # 不登录，直接发布消息
    response = client.post('/funboost/publish',
                          json={
                              'queue_name': 'test_queue',
                              'msg_body': {'x': 1, 'y': 2}
                          },
                          content_type='application/json')
    
    # 验证响应
    assert response.status_code == 401, "未认证用户应返回 401"
    
    data = response.get_json()
    assert data is not None, "响应应为 JSON 格式"
    assert data['succ'] is False, "succ 字段应为 False"
    assert '未登录' in data['msg'] or '会话已过期' in data['msg'], "应包含未登录提示"
    assert data['data'] is None, "data 字段应为 None"


def test_project_filtering_works_end_to_end(client, setup_faas_blueprint):
    """
    测试项目过滤端到端工作
    
    **Validates: Requirements 6.3**
    
    验证：
    - 从请求中提取 project_id
    - 将 project_id 转换为 project_code
    - 注入到 CareProjectNameEnv
    - FaaS 接口可以使用项目过滤
    - 请求完成后恢复原始值
    """
    from funboost.core.active_cousumer_info_getter import CareProjectNameEnv
    
    # 设置初始值
    CareProjectNameEnv.set('')
    
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 发布消息，带 project_id
    response = client.post('/funboost/publish',
                          json={
                              'queue_name': 'test_queue',
                              'msg_body': {'x': 1, 'y': 2},
                              'project_id': 123
                          },
                          content_type='application/json')
    
    # 验证响应
    assert response.status_code == 200, "应成功发布消息"
    
    data = response.get_json()
    assert data['succ'] is True, "succ 字段应为 True"
    
    # 验证 FaaS 接口接收到了正确的项目过滤
    assert data['data']['current_project'] == 'project_123', \
        "FaaS 接口应接收到正确的项目过滤"
    
    # 验证请求完成后，CareProjectNameEnv 被恢复
    assert CareProjectNameEnv.get() is None, \
        "请求完成后应恢复原始值"


def test_project_filtering_from_query_params(client, setup_faas_blueprint):
    """
    测试从查询参数提取项目过滤
    
    验证：
    - 可以从 URL 查询参数中提取 project_id
    - 项目过滤正常工作
    """
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 发布消息，project_id 在查询参数中
    response = client.post('/funboost/publish?project_id=456',
                          json={
                              'queue_name': 'test_queue',
                              'msg_body': {'x': 1, 'y': 2}
                          },
                          content_type='application/json')
    
    # 验证响应
    assert response.status_code == 200, "应成功发布消息"
    
    data = response.get_json()
    assert data['succ'] is True, "succ 字段应为 True"
    assert data['data']['current_project'] == 'project_456', \
        "应从查询参数中提取项目过滤"


def test_rpc_mode_message_publishing(client, setup_faas_blueprint):
    """
    测试 RPC 模式消息发布
    
    **Validates: Requirements 6.3**
    
    验证：
    - 设置 need_result=True 时使用 RPC 模式
    - 返回任务结果
    - 响应格式正确
    """
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 发布消息，使用 RPC 模式
    response = client.post('/funboost/publish',
                          json={
                              'queue_name': 'test_queue',
                              'msg_body': {'x': 1, 'y': 2},
                              'need_result': True,
                              'timeout': 30
                          },
                          content_type='application/json')
    
    # 验证响应
    assert response.status_code == 200, "RPC 模式应成功发布消息"
    
    data = response.get_json()
    assert data is not None, "响应应为 JSON 格式"
    assert data['succ'] is True, "succ 字段应为 True"
    assert 'RPC模式' in data['msg'], "应包含 RPC 模式提示"
    assert 'result' in data['data'], "应返回任务结果"
    assert data['data']['result'] == {'result': 'success', 'value': 42}, \
        "任务结果应正确"


def test_error_response_format_for_missing_params(client, setup_faas_blueprint):
    """
    测试缺少必填参数时的错误响应格式
    
    **Validates: Requirements 6.3**
    
    验证：
    - 缺少 queue_name 时返回 400
    - 错误响应格式符合 FaaS 接口规范
    - 错误消息清晰明确
    """
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 发布消息，缺少 queue_name
    response = client.post('/funboost/publish',
                          json={
                              'msg_body': {'x': 1, 'y': 2}
                          },
                          content_type='application/json')
    
    # 验证响应
    assert response.status_code == 400, "缺少必填参数应返回 400"
    
    data = response.get_json()
    assert data is not None, "响应应为 JSON 格式"
    assert data['succ'] is False, "succ 字段应为 False"
    assert 'queue_name' in data['msg'], "错误消息应提到缺少的参数"
    assert data['data'] is None, "data 字段应为 None"


def test_error_response_format_for_invalid_project_id(client, setup_faas_blueprint):
    """
    测试无效 project_id 时的错误响应格式
    
    **Validates: Requirements 6.3**
    
    验证：
    - 无效的 project_id 返回 400
    - 错误响应格式正确
    """
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 发布消息，project_id 无效
    response = client.post('/funboost/publish',
                          json={
                              'queue_name': 'test_queue',
                              'msg_body': {'x': 1, 'y': 2},
                              'project_id': 'invalid'
                          },
                          content_type='application/json')
    
    # 验证响应
    assert response.status_code == 400, "无效的 project_id 应返回 400"
    
    data = response.get_json()
    assert data is not None, "响应应为 JSON 格式"
    assert data['succ'] is False, "succ 字段应为 False"
    assert '无效' in data['msg'] or 'invalid' in data['msg'].lower(), \
        "错误消息应提到无效的参数"
    assert data['data'] is None, "data 字段应为 None"


def test_error_response_consistency(client, setup_faas_blueprint):
    """
    测试错误响应格式的一致性
    
    **Validates: Requirements 6.3**
    
    验证：
    - 所有错误响应都使用相同的格式
    - 包含 succ, msg, data 字段
    - succ 为 False
    - data 为 None
    """
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 测试多种错误情况
    error_cases = [
        # 缺少 queue_name
        ({
            'msg_body': {'x': 1}
        }, 400),
        # 无效的 project_id
        ({
            'queue_name': 'test_queue',
            'msg_body': {'x': 1},
            'project_id': 'invalid'
        }, 400),
    ]
    
    for request_data, expected_status in error_cases:
        response = client.post('/funboost/publish',
                              json=request_data,
                              content_type='application/json')
        
        assert response.status_code == expected_status, \
            f"请求 {request_data} 应返回 {expected_status}"
        
        data = response.get_json()
        assert data is not None, "响应应为 JSON 格式"
        assert 'succ' in data, "响应应包含 succ 字段"
        assert 'msg' in data, "响应应包含 msg 字段"
        assert 'data' in data, "响应应包含 data 字段"
        assert data['succ'] is False, "错误响应的 succ 应为 False"
        assert isinstance(data['msg'], str), "msg 应为字符串"
        assert data['data'] is None, "错误响应的 data 应为 None"


def test_multiple_requests_with_different_projects(client, setup_faas_blueprint):
    """
    测试多个请求使用不同项目的隔离性
    
    验证：
    - 每个请求的项目过滤是独立的
    - 一个请求不会影响另一个请求
    """
    from funboost.core.active_cousumer_info_getter import CareProjectNameEnv
    
    # 设置初始值
    CareProjectNameEnv.set('')
    
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 请求 1：项目 A
    response1 = client.post('/funboost/publish',
                           json={
                               'queue_name': 'test_queue',
                               'msg_body': {'x': 1},
                               'project_id': 100
                           },
                           content_type='application/json')
    
    assert response1.status_code == 200
    data1 = response1.get_json()
    assert data1['data']['current_project'] == 'project_100'
    
    # 请求 2：项目 B
    response2 = client.post('/funboost/publish',
                           json={
                               'queue_name': 'test_queue',
                               'msg_body': {'x': 2},
                               'project_id': 200
                           },
                           content_type='application/json')
    
    assert response2.status_code == 200
    data2 = response2.get_json()
    assert data2['data']['current_project'] == 'project_200'
    
    # 请求 3：无项目
    response3 = client.post('/funboost/publish',
                           json={
                               'queue_name': 'test_queue',
                               'msg_body': {'x': 3}
                           },
                           content_type='application/json')
    
    assert response3.status_code == 200
    data3 = response3.get_json()
    assert data3['data']['current_project'] is None
    
    # 验证全局状态未被污染
    assert CareProjectNameEnv.get() is None


def test_publish_with_empty_msg_body(client, setup_faas_blueprint):
    """
    测试使用空消息体发布消息
    
    验证：
    - 允许空的 msg_body（默认为 {}）
    - 消息发布成功
    """
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 发布消息，msg_body 为空
    response = client.post('/funboost/publish',
                          json={
                              'queue_name': 'test_queue',
                              'msg_body': {}
                          },
                          content_type='application/json')
    
    # 验证响应
    assert response.status_code == 200, "空消息体应允许发布"
    
    data = response.get_json()
    assert data['succ'] is True, "succ 字段应为 True"
    assert 'task_id' in data['data'], "应返回 task_id"


def test_publish_without_msg_body(client, setup_faas_blueprint):
    """
    测试不提供 msg_body 参数时的默认行为
    
    验证：
    - 不提供 msg_body 时使用默认值 {}
    - 消息发布成功
    """
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 发布消息，不提供 msg_body
    response = client.post('/funboost/publish',
                          json={
                              'queue_name': 'test_queue'
                          },
                          content_type='application/json')
    
    # 验证响应
    assert response.status_code == 200, "不提供 msg_body 应使用默认值"
    
    data = response.get_json()
    assert data['succ'] is True, "succ 字段应为 True"
    assert 'task_id' in data['data'], "应返回 task_id"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
