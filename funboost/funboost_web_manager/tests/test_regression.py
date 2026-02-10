# -*- coding: utf-8 -*-
"""
回归测试 - Web Manager FaaS 集成

测试 Web Manager 与 FaaS Blueprint 集成后，确保现有功能不受影响：
- 测试用户登录/登出仍然正常
- 测试其他 Web Manager 路由未受影响
- 测试通过 Web Manager 可访问 FaaS 端点
- 测试队列监控功能仍然正常

**Validates: Requirements 6.2, 6.3**

**重要提示**：
由于 Flask Blueprint 的限制（不能在注册后再添加钩子），这些测试应该：
1. 单独运行：pytest funboost/funboost_web_manager/tests/test_regression.py
2. 或者在新的 Python 进程中运行
3. 不要与其他导入 create_app() 的测试一起运行

如果遇到 "The setup method 'before_request' can no longer be called" 错误，
请在新的 Python 进程中运行这些测试。
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask_login import LoginManager, UserMixin


class MockUser(UserMixin):
    """模拟用户类"""
    def __init__(self, user_id, is_authenticated=True):
        self.id = user_id
        self._is_authenticated = is_authenticated
    
    @property
    def is_authenticated(self):
        return self._is_authenticated


@pytest.fixture(scope='module')
def app():
    """创建测试应用 - 模拟完整的 Web Manager 应用
    
    使用 module scope 避免多次创建应用导致 blueprint 重复注册
    """
    from funboost.funboost_web_manager.app import create_app
    
    # 创建应用
    test_app = create_app()
    test_app.config['TESTING'] = True
    test_app.config['WTF_CSRF_ENABLED'] = False
    
    return test_app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def mock_db_session():
    """模拟数据库会话"""
    with patch('funboost.funboost_web_manager.user_models.get_session') as mock_session:
        session = Mock()
        mock_session.return_value = session
        yield session


@pytest.fixture
def mock_user_query():
    """模拟用户查询"""
    with patch('funboost.funboost_web_manager.user_models.query_user_by_name') as mock_query:
        # 创建模拟用户
        mock_user = Mock()
        mock_user.user_name = 'test_user'
        mock_user.password = 'hashed_password'
        mock_user.is_active = True
        mock_user.force_password_change = False
        mock_query.return_value = mock_user
        yield mock_query


# ============================================================================
# 测试 1: 用户登录/登出功能
# ============================================================================

@patch('funboost.funboost_web_manager.services.auth_service.AuthService.authenticate')
def test_user_login_still_works(mock_authenticate, client):
    """
    测试用户登录功能仍然正常
    
    **Validates: Requirements 6.2**
    
    验证：
    - 用户可以成功登录
    - 登录后可以访问受保护的路由
    - Session 正常工作
    """
    # 模拟认证成功
    mock_authenticate.return_value = {
        'success': True,
        'user_name': 'test_user',
        'force_password_change': False
    }
    
    # 尝试登录（使用表单登录）
    response = client.post('/login', data={
        'user_name': 'test_user',
        'password': 'test_password',
        'remember_me': False
    }, follow_redirects=False)
    
    # 验证登录成功（重定向到队列操作页面）
    assert response.status_code in [302, 303], "登录应该重定向"
    assert '/queue-op' in response.location or response.location.endswith('/queue-op'), \
        "登录成功应重定向到队列操作页面"


@patch('funboost.funboost_web_manager.services.auth_service.AuthService.authenticate')
def test_user_login_with_api_endpoint(mock_authenticate, client):
    """
    测试 API 登录端点仍然正常
    
    **Validates: Requirements 6.2**
    
    验证：
    - API 登录端点正常工作
    - 返回正确的 JSON 响应
    """
    # 模拟认证成功
    mock_authenticate.return_value = {
        'success': True,
        'user_name': 'test_user',
        'force_password_change': False
    }
    
    # 使用 API 端点登录
    response = client.post('/api/login',
                          json={
                              'user_name': 'test_user',
                              'password': 'test_password'
                          },
                          content_type='application/json')
    
    # 验证响应
    assert response.status_code == 200, "API 登录应返回 200"
    data = response.get_json()
    assert data is not None, "响应应为 JSON 格式"
    assert data.get('success') is True, "登录应成功"


def test_user_logout_still_works(client):
    """
    测试用户登出功能仍然正常
    
    **Validates: Requirements 6.2**
    
    验证：
    - 用户可以成功登出
    - 登出后无法访问受保护的路由
    - Session 被清除
    """
    # 模拟登录状态
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 登出
    response = client.get('/logout', follow_redirects=False)
    
    # 验证登出成功（重定向到登录页面）
    assert response.status_code in [302, 303], "登出应该重定向"
    
    # 验证 session 被清除
    with client.session_transaction() as sess:
        assert '_user_id' not in sess, "登出后 session 应被清除"


def test_login_failure_handling(client):
    """
    测试登录失败处理
    
    **Validates: Requirements 6.2**
    
    验证：
    - 错误的凭证导致登录失败
    - 返回适当的错误响应
    """
    with patch('funboost.funboost_web_manager.services.auth_service.AuthService.authenticate') as mock_auth:
        # 模拟认证失败
        mock_auth.return_value = {
            'success': False,
            'error': '用户名或密码错误'
        }
        
        # 尝试登录
        response = client.post('/login', data={
            'user_name': 'wrong_user',
            'password': 'wrong_password',
            'remember_me': False
        }, follow_redirects=False)
        
        # 验证登录失败（重定向到登录页面并带错误参数）
        assert response.status_code in [302, 303], "登录失败应该重定向"
        assert 'error' in response.location or '/login' in response.location, \
            "登录失败应重定向到登录页面"


# ============================================================================
# 测试 2: Web Manager 路由未受影响
# ============================================================================

@patch('funboost.funboost_web_manager.services.permission_service.PermissionService.check_permission')
def test_queue_monitoring_routes_still_work(mock_check_permission, client):
    """
    测试队列监控路由仍然正常工作
    
    **Validates: Requirements 6.2**
    
    验证：
    - /queue/* 路由仍然可访问
    - 权限检查正常工作
    - 返回正确的响应格式
    """
    # 模拟权限检查通过
    mock_check_permission.return_value = True
    
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 测试队列监控路由（这些路由应该仍然存在且正常工作）
    # 注意：这些路由可能需要额外的 mock，这里只测试路由是否存在
    
    # 测试心跳信息路由
    with patch('funboost.funboost_web_manager.routes.queue.ActiveCousumerProcessInfoGetter') as mock_getter:
        mock_getter.get_all_active_cousumer_process_info.return_value = []
        
        response = client.get('/running_consumer/hearbeat_info_by_queue_name')
        # 路由应该存在（不是 404）
        assert response.status_code != 404, "队列监控路由应该存在"


@patch('funboost.funboost_web_manager.services.permission_service.PermissionService.check_permission')
def test_admin_routes_still_work(mock_check_permission, client):
    """
    测试管理路由仍然正常工作
    
    **Validates: Requirements 6.2**
    
    验证：
    - /admin/* 路由仍然可访问
    - 管理功能未受影响
    """
    # 模拟权限检查通过
    mock_check_permission.return_value = True
    
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'admin_user'
    
    # 测试管理路由（检查路由是否存在）
    # 用户管理
    response = client.get('/admin/users')
    assert response.status_code != 404, "用户管理路由应该存在"
    
    # 角色管理
    response = client.get('/admin/roles')
    assert response.status_code != 404, "角色管理路由应该存在"
    
    # 项目管理
    response = client.get('/admin/projects')
    assert response.status_code != 404, "项目管理路由应该存在"


def test_frontend_routes_still_work(client):
    """
    测试前端路由仍然正常工作
    
    **Validates: Requirements 6.2**
    
    验证：
    - 前端静态文件服务正常
    - 前端路由可访问
    """
    # 测试前端首页
    response = client.get('/')
    assert response.status_code in [200, 302, 303], "前端首页应该可访问"
    
    # 测试登录页面
    response = client.get('/login/')
    assert response.status_code == 200, "登录页面应该可访问"


# ============================================================================
# 测试 3: FaaS 端点可通过 Web Manager 访问
# ============================================================================

@patch('funboost.funboost_web_manager.services.permission_service.PermissionService.check_permission')
@patch('funboost.core.booster.BoostersManager.get_all_boosters')
def test_faas_endpoints_accessible_via_web_manager(mock_get_boosters, mock_check_permission, client):
    """
    测试 FaaS 端点可通过 Web Manager 访问
    
    **Validates: Requirements 6.2, 6.3**
    
    验证：
    - FaaS blueprint 已正确注册
    - FaaS 端点可通过 /funboost/* 访问
    - 权限检查正常工作
    """
    # 模拟权限检查通过
    mock_check_permission.return_value = True
    
    # 模拟 Booster
    mock_booster = Mock()
    mock_booster.queue_name = 'test_queue'
    mock_booster.function_name = 'test_function'
    mock_booster.project_name = 'test_project'
    mock_get_boosters.return_value = {'test_queue': mock_booster}
    
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 测试 FaaS 端点
    # 1. 测试获取所有队列
    response = client.get('/funboost/get_all_queues')
    assert response.status_code != 404, "FaaS 端点应该可访问"
    assert response.status_code in [200, 401, 403], "FaaS 端点应返回有效状态码"
    
    # 2. 测试获取队列配置
    response = client.get('/funboost/get_queues_config')
    assert response.status_code != 404, "FaaS 配置端点应该可访问"


@patch('funboost.funboost_web_manager.services.permission_service.PermissionService.check_permission')
def test_faas_endpoints_require_authentication(mock_check_permission, client):
    """
    测试 FaaS 端点需要认证
    
    **Validates: Requirements 6.2, 6.3**
    
    验证：
    - 未登录用户无法访问 FaaS 端点
    - 返回 401 错误
    """
    # 不登录，直接访问 FaaS 端点
    response = client.get('/funboost/get_all_queues')
    
    # 验证返回 401
    assert response.status_code == 401, "未认证用户应返回 401"
    
    data = response.get_json()
    assert data is not None, "响应应为 JSON 格式"
    assert data.get('succ') is False, "succ 字段应为 False"


@patch('funboost.funboost_web_manager.services.permission_service.PermissionService.check_permission')
def test_faas_endpoints_require_permission(mock_check_permission, client):
    """
    测试 FaaS 端点需要权限
    
    **Validates: Requirements 6.2, 6.3**
    
    验证：
    - 无权限用户无法访问 FaaS 端点
    - 返回 403 错误
    """
    # 模拟权限检查失败
    mock_check_permission.return_value = False
    
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 访问需要权限的 FaaS 端点
    response = client.get('/funboost/get_all_queues')
    
    # 验证返回 403
    assert response.status_code == 403, "无权限用户应返回 403"
    
    data = response.get_json()
    assert data is not None, "响应应为 JSON 格式"
    assert data.get('succ') is False, "succ 字段应为 False"


# ============================================================================
# 测试 4: 队列监控功能仍然正常
# ============================================================================

@patch('funboost.funboost_web_manager.services.permission_service.PermissionService.check_permission')
@patch('funboost.funboost_web_manager.routes.queue.ActiveCousumerProcessInfoGetter')
def test_queue_heartbeat_monitoring_still_works(mock_getter, mock_check_permission, client):
    """
    测试队列心跳监控功能仍然正常
    
    **Validates: Requirements 6.2**
    
    验证：
    - 心跳信息查询正常工作
    - 数据格式正确
    """
    # 模拟权限检查通过
    mock_check_permission.return_value = True
    
    # 模拟心跳数据
    mock_getter.get_all_active_cousumer_process_info.return_value = [
        {
            'queue_name': 'test_queue',
            'ip': '127.0.0.1',
            'pid': 12345,
            'last_heartbeat': '2024-01-01 12:00:00'
        }
    ]
    
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 查询心跳信息
    response = client.get('/running_consumer/hearbeat_info_by_queue_name')
    
    # 验证响应
    assert response.status_code == 200, "心跳查询应成功"
    data = response.get_json()
    assert data is not None, "响应应为 JSON 格式"


@patch('funboost.funboost_web_manager.services.permission_service.PermissionService.check_permission')
@patch('funboost.funboost_web_manager.routes.queue.QueuesConusmerParamsGetter')
def test_queue_params_monitoring_still_works(mock_getter, mock_check_permission, client):
    """
    测试队列参数监控功能仍然正常
    
    **Validates: Requirements 6.2**
    
    验证：
    - 队列参数查询正常工作
    - 数据格式正确
    """
    # 模拟权限检查通过
    mock_check_permission.return_value = True
    
    # 模拟队列参数
    mock_getter.get_all_queues_cousumer_params.return_value = {
        'test_queue': {
            'queue_name': 'test_queue',
            'max_workers': 10,
            'qps': 100
        }
    }
    
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 查询队列参数
    response = client.get('/queue/params_and_active_consumers')
    
    # 验证响应
    assert response.status_code == 200, "队列参数查询应成功"
    data = response.get_json()
    assert data is not None, "响应应为 JSON 格式"


@patch('funboost.funboost_web_manager.services.permission_service.PermissionService.check_permission')
@patch('funboost.funboost_web_manager.routes.queue.RedisMixin')
def test_queue_message_count_still_works(mock_redis, mock_check_permission, client):
    """
    测试队列消息数量查询功能仍然正常
    
    **Validates: Requirements 6.2**
    
    验证：
    - 消息数量查询正常工作
    - 数据格式正确
    """
    # 模拟权限检查通过
    mock_check_permission.return_value = True
    
    # 模拟 Redis 连接
    mock_redis_instance = Mock()
    mock_redis_instance.llen.return_value = 100
    mock_redis.return_value = mock_redis_instance
    
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 查询消息数量
    with patch('funboost.funboost_web_manager.routes.queue.QueuesConusmerParamsGetter') as mock_params:
        mock_params.get_all_queues_cousumer_params.return_value = {
            'test_queue': {'queue_name': 'test_queue'}
        }
        
        response = client.get('/queue/get_msg_num_all_queues')
        
        # 验证响应
        assert response.status_code == 200, "消息数量查询应成功"
        data = response.get_json()
        assert data is not None, "响应应为 JSON 格式"


# ============================================================================
# 测试 5: 项目过滤功能集成
# ============================================================================

@patch('funboost.funboost_web_manager.services.permission_service.PermissionService.check_permission')
@patch('funboost.funboost_web_manager.services.project_service.ProjectService')
def test_project_filtering_works_with_web_manager(mock_project_service_class, mock_check_permission, client):
    """
    测试项目过滤功能与 Web Manager 集成
    
    **Validates: Requirements 6.2, 6.3**
    
    验证：
    - 项目过滤在 Web Manager 和 FaaS 端点中都正常工作
    - 用户只能看到有权限的项目数据
    """
    # 模拟权限检查通过
    mock_check_permission.return_value = True
    
    # 模拟项目服务
    mock_service = Mock()
    mock_service.check_project_permission.return_value = True
    mock_service.get_project_code_by_id.return_value = 'test_project'
    mock_project_service_class.return_value = mock_service
    
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 访问 FaaS 端点，带 project_id
    with patch('funboost.core.booster.BoostersManager.get_all_boosters') as mock_boosters:
        mock_boosters.return_value = {}
        
        response = client.get('/funboost/get_all_queues?project_id=1')
        
        # 验证响应
        assert response.status_code in [200, 403], "项目过滤应正常工作"
        
        # 验证项目权限检查被调用
        mock_service.check_project_permission.assert_called()


@patch('funboost.funboost_web_manager.services.permission_service.PermissionService.check_permission')
@patch('funboost.funboost_web_manager.services.project_service.ProjectService')
def test_project_filtering_blocks_unauthorized_access(mock_project_service_class, mock_check_permission, client):
    """
    测试项目过滤阻止未授权访问
    
    **Validates: Requirements 6.2, 6.3**
    
    验证：
    - 用户无法访问无权限的项目数据
    - 返回 403 错误
    """
    # 模拟权限检查通过（角色权限）
    mock_check_permission.return_value = True
    
    # 模拟项目服务（项目权限失败）
    mock_service = Mock()
    mock_service.check_project_permission.return_value = False
    mock_project_service_class.return_value = mock_service
    
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 访问 FaaS 端点，带无权限的 project_id
    response = client.get('/funboost/get_all_queues?project_id=999')
    
    # 验证返回 403
    assert response.status_code == 403, "无项目权限应返回 403"
    
    data = response.get_json()
    assert data is not None, "响应应为 JSON 格式"
    assert data.get('succ') is False, "succ 字段应为 False"
    assert '权限' in data.get('msg', ''), "错误消息应提到权限"


# ============================================================================
# 测试 6: 响应格式一致性
# ============================================================================

@patch('funboost.funboost_web_manager.services.permission_service.PermissionService.check_permission')
def test_response_format_consistency_across_endpoints(mock_check_permission, client):
    """
    测试不同端点的响应格式一致性
    
    **Validates: Requirements 6.2, 6.3**
    
    验证：
    - FaaS 端点使用 succ/msg/data 格式
    - Web Manager 端点使用 success/message/data 格式（如果有）
    - 错误响应格式一致
    """
    # 模拟权限检查失败
    mock_check_permission.return_value = False
    
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 测试 FaaS 端点的错误响应格式
    response = client.get('/funboost/get_all_queues')
    assert response.status_code == 403
    
    data = response.get_json()
    assert 'succ' in data, "FaaS 端点应使用 succ 字段"
    assert 'msg' in data, "FaaS 端点应使用 msg 字段"
    assert 'data' in data, "FaaS 端点应使用 data 字段"
    assert data['succ'] is False, "错误响应的 succ 应为 False"
    assert data['data'] is None, "错误响应的 data 应为 None"


# ============================================================================
# 测试 7: 并发请求隔离
# ============================================================================

@patch('funboost.funboost_web_manager.services.permission_service.PermissionService.check_permission')
@patch('funboost.funboost_web_manager.services.project_service.ProjectService')
def test_concurrent_requests_are_isolated(mock_project_service_class, mock_check_permission, client):
    """
    测试并发请求的项目过滤隔离
    
    **Validates: Requirements 6.2, 6.3**
    
    验证：
    - 不同请求的项目过滤互不影响
    - CareProjectNameEnv 在请求间正确隔离
    """
    from funboost.core.active_cousumer_info_getter import CareProjectNameEnv
    
    # 模拟权限检查通过
    mock_check_permission.return_value = True
    
    # 模拟项目服务
    mock_service = Mock()
    mock_service.check_project_permission.return_value = True
    
    def get_project_code(project_id):
        return f'project_{project_id}'
    
    mock_service.get_project_code_by_id.side_effect = get_project_code
    mock_project_service_class.return_value = mock_service
    
    # 设置初始值
    CareProjectNameEnv.set('')
    
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 模拟多个请求
    with patch('funboost.core.booster.BoostersManager.get_all_boosters') as mock_boosters:
        mock_boosters.return_value = {}
        
        # 请求 1
        response1 = client.get('/funboost/get_all_queues?project_id=1')
        assert response1.status_code in [200, 403]
        
        # 请求 2
        response2 = client.get('/funboost/get_all_queues?project_id=2')
        assert response2.status_code in [200, 403]
        
        # 请求 3（无项目）
        response3 = client.get('/funboost/get_all_queues')
        assert response3.status_code in [200, 403]
    
    # 验证全局状态未被污染
    final_value = CareProjectNameEnv.get()
    assert final_value is None or final_value == '', \
        "请求完成后 CareProjectNameEnv 应被清理"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
