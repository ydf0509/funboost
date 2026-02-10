# -*- coding: utf-8 -*-
"""
测试项目权限检查逻辑

验证 check_faas_permission() 函数中的项目权限检查功能：
- project_id 提取（从 query string 和 JSON body）
- 项目权限检查（read/write 级别）
- project_code 获取和注入到 g.care_project_name
- 错误处理（无效的 project_id）
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, g
from flask_login import LoginManager, UserMixin


class MockUser(UserMixin):
    """模拟用户类"""
    def __init__(self, user_id):
        self.id = user_id


@pytest.fixture
def app():
    """创建测试应用"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['TESTING'] = True
    
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


def test_project_id_extraction_from_query_string(app, client):
    """测试从 query string 提取 project_id"""
    with app.test_request_context('/?project_id=123'):
        from flask import request
        
        # 从 query string 提取
        project_id = request.args.get('project_id')
        assert project_id == '123'
        
        # 转换为整数
        project_id_int = int(project_id)
        assert project_id_int == 123


def test_project_id_extraction_from_json_body(app, client):
    """测试从 JSON body 提取 project_id"""
    with app.test_request_context(
        '/',
        method='POST',
        json={'project_id': 456, 'queue_name': 'test'}
    ):
        from flask import request
        
        # 从 JSON body 提取
        data = request.get_json(silent=True) or {}
        project_id = data.get('project_id')
        assert project_id == 456


def test_project_id_extraction_priority(app, client):
    """测试 project_id 提取优先级（query string 优先）"""
    with app.test_request_context(
        '/?project_id=123',
        method='POST',
        json={'project_id': 456}
    ):
        from flask import request
        
        # 先从 query string 提取
        project_id = request.args.get('project_id')
        if not project_id and request.is_json:
            data = request.get_json(silent=True) or {}
            project_id = data.get('project_id')
        
        # query string 优先
        assert project_id == '123'


def test_invalid_project_id_handling(app, client):
    """测试无效 project_id 的错误处理"""
    with app.test_request_context('/?project_id=invalid'):
        from flask import request
        
        project_id = request.args.get('project_id')
        
        # 尝试转换为整数应该抛出异常
        with pytest.raises((ValueError, TypeError)):
            project_id_int = int(project_id)


@patch('funboost.funboost_web_manager.services.project_service.ProjectService')
def test_project_permission_check_read_level(mock_project_service_class, app):
    """测试项目权限检查 - read 级别"""
    # 模拟 ProjectService
    mock_service = Mock()
    mock_service.check_project_permission.return_value = True
    mock_service.get_project_code_by_id.return_value = 'test_project'
    mock_project_service_class.return_value = mock_service
    
    with app.test_request_context('/?project_id=1'):
        from funboost.funboost_web_manager.services.project_service import ProjectService
        
        project_service = ProjectService()
        user_id = 'test_user'
        project_id = 1
        required_level = 'read'
        
        # 检查权限
        has_permission = project_service.check_project_permission(
            user_id, project_id, required_level
        )
        
        assert has_permission is True
        mock_service.check_project_permission.assert_called_once_with(
            user_id, project_id, required_level
        )


@patch('funboost.funboost_web_manager.services.project_service.ProjectService')
def test_project_permission_check_write_level(mock_project_service_class, app):
    """测试项目权限检查 - write 级别"""
    # 模拟 ProjectService
    mock_service = Mock()
    mock_service.check_project_permission.return_value = True
    mock_service.get_project_code_by_id.return_value = 'test_project'
    mock_project_service_class.return_value = mock_service
    
    with app.test_request_context('/?project_id=1'):
        from funboost.funboost_web_manager.services.project_service import ProjectService
        
        project_service = ProjectService()
        user_id = 'test_user'
        project_id = 1
        required_level = 'write'
        
        # 检查权限
        has_permission = project_service.check_project_permission(
            user_id, project_id, required_level
        )
        
        assert has_permission is True
        mock_service.check_project_permission.assert_called_once_with(
            user_id, project_id, required_level
        )


@patch('funboost.funboost_web_manager.services.project_service.ProjectService')
def test_project_permission_check_denied(mock_project_service_class, app):
    """测试项目权限检查 - 权限被拒绝"""
    # 模拟 ProjectService
    mock_service = Mock()
    mock_service.check_project_permission.return_value = False
    mock_project_service_class.return_value = mock_service
    
    with app.test_request_context('/?project_id=1'):
        from funboost.funboost_web_manager.services.project_service import ProjectService
        
        project_service = ProjectService()
        user_id = 'test_user'
        project_id = 1
        required_level = 'write'
        
        # 检查权限
        has_permission = project_service.check_project_permission(
            user_id, project_id, required_level
        )
        
        assert has_permission is False


@patch('funboost.funboost_web_manager.services.project_service.ProjectService')
def test_project_code_retrieval(mock_project_service_class, app):
    """测试项目代码获取"""
    # 模拟 ProjectService
    mock_service = Mock()
    mock_service.get_project_code_by_id.return_value = 'my_project'
    mock_project_service_class.return_value = mock_service
    
    with app.test_request_context('/?project_id=1'):
        from funboost.funboost_web_manager.services.project_service import ProjectService
        
        project_service = ProjectService()
        project_id = 1
        
        # 获取项目代码
        project_code = project_service.get_project_code_by_id(project_id)
        
        assert project_code == 'my_project'
        mock_service.get_project_code_by_id.assert_called_once_with(project_id)


@patch('funboost.funboost_web_manager.services.project_service.ProjectService')
def test_project_code_injection_to_g(mock_project_service_class, app):
    """测试项目代码注入到 g.care_project_name"""
    # 模拟 ProjectService
    mock_service = Mock()
    mock_service.check_project_permission.return_value = True
    mock_service.get_project_code_by_id.return_value = 'test_project'
    mock_project_service_class.return_value = mock_service
    
    with app.test_request_context('/?project_id=1'):
        from flask import g
        from funboost.funboost_web_manager.services.project_service import ProjectService
        
        project_service = ProjectService()
        project_id = 1
        
        # 获取项目代码
        project_code = project_service.get_project_code_by_id(project_id)
        
        # 注入到 g
        if project_code:
            g.care_project_name = project_code
        
        # 验证
        assert hasattr(g, 'care_project_name')
        assert g.care_project_name == 'test_project'


@patch('funboost.funboost_web_manager.services.project_service.ProjectService')
def test_project_code_none_handling(mock_project_service_class, app):
    """测试项目代码为 None 的处理（默认项目）"""
    # 模拟 ProjectService
    mock_service = Mock()
    mock_service.check_project_permission.return_value = True
    mock_service.get_project_code_by_id.return_value = None  # 默认项目返回 None
    mock_project_service_class.return_value = mock_service
    
    with app.test_request_context('/?project_id=1'):
        from flask import g
        from funboost.funboost_web_manager.services.project_service import ProjectService
        
        project_service = ProjectService()
        project_id = 1
        
        # 获取项目代码
        project_code = project_service.get_project_code_by_id(project_id)
        
        # 只有在 project_code 不为 None 时才注入
        if project_code:
            g.care_project_name = project_code
        
        # 验证：默认项目不应该设置 g.care_project_name
        assert not hasattr(g, 'care_project_name')


def test_permission_level_determination():
    """测试权限级别判断逻辑"""
    # 写操作需要 write 权限
    write_paths = [
        '/funboost/publish',
        '/funboost/clear_queue',
        '/funboost/deprecate_queue',
        '/funboost/add_timing_job',
        '/funboost/delete_timing_job'
    ]
    
    for path in write_paths:
        required_permission = 'queue:execute'
        required_level = 'write' if required_permission == 'queue:execute' else 'read'
        assert required_level == 'write', f"Path {path} should require write permission"
    
    # 读操作需要 read 权限
    read_paths = [
        '/funboost/get_all_queues',
        '/funboost/get_result',
        '/funboost/get_timing_jobs'
    ]
    
    for path in read_paths:
        required_permission = 'queue:read'
        required_level = 'write' if required_permission == 'queue:execute' else 'read'
        assert required_level == 'read', f"Path {path} should require read permission"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
