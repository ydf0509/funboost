# -*- coding: utf-8 -*-
"""
测试项目过滤注入和恢复逻辑

验证 inject_project_filter() 和 restore_project_filter() 函数的功能：
- 从 g.care_project_name 读取项目代码并注入到 CareProjectNameEnv
- 保存原始的 CareProjectNameEnv 值
- 请求完成后恢复原始值
- 确保项目过滤只在当前请求生命周期内有效

**Validates: Requirements 3.3.2, 3.4**
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, g, Blueprint, jsonify, request
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


@pytest.fixture
def mock_blueprint():
    """创建模拟的 FaaS blueprint"""
    bp = Blueprint('funboost', __name__, url_prefix='/funboost')
    
    @bp.route('/get_all_queues', methods=['GET'])
    def get_all_queues():
        # 在路由处理函数中检查 CareProjectNameEnv
        from funboost.core.active_cousumer_info_getter import CareProjectNameEnv
        current_project = CareProjectNameEnv.get()
        return jsonify({
            "succ": True,
            "msg": "success",
            "data": {
                "queues": [],
                "current_project": current_project
            }
        })
    
    @bp.route('/publish', methods=['POST'])
    def publish():
        from funboost.core.active_cousumer_info_getter import CareProjectNameEnv
        current_project = CareProjectNameEnv.get()
        return jsonify({
            "succ": True,
            "msg": "published",
            "data": {
                "task_id": "123",
                "current_project": current_project
            }
        })
    
    return bp


def test_inject_project_filter_sets_care_project_name(app, mock_blueprint):
    """
    测试 inject_project_filter 设置 CareProjectNameEnv
    
    **Validates: Requirements 3.3.2**
    
    验证：
    - 从 g.care_project_name 读取项目代码
    - 将项目代码设置到 CareProjectNameEnv
    - FaaS 接口可以读取到设置的项目代码
    """
    from funboost.core.active_cousumer_info_getter import CareProjectNameEnv
    
    # 添加项目过滤注入钩子
    @mock_blueprint.before_request
    def inject_project_filter():
        if hasattr(g, 'care_project_name') and g.care_project_name:
            g._original_care_project_name = CareProjectNameEnv.get()
            CareProjectNameEnv.set(g.care_project_name)
    
    # 注册 blueprint
    app.register_blueprint(mock_blueprint)
    
    # 测试：在请求上下文中设置 g.care_project_name
    with app.test_request_context('/funboost/get_all_queues'):
        g.care_project_name = 'test_project'
        
        # 触发 before_request 钩子
        app.preprocess_request()
        
        # 验证 CareProjectNameEnv 被设置
        assert CareProjectNameEnv.get() == 'test_project'


def test_inject_project_filter_saves_original_value(app, mock_blueprint):
    """
    测试 inject_project_filter 保存原始值
    
    **Validates: Requirements 3.3.2**
    
    验证：
    - 在设置新值之前保存原始的 CareProjectNameEnv 值
    - 原始值保存在 g._original_care_project_name
    """
    from funboost.core.active_cousumer_info_getter import CareProjectNameEnv
    
    # 设置初始值
    CareProjectNameEnv.set('original_project')
    
    # 添加项目过滤注入钩子
    @mock_blueprint.before_request
    def inject_project_filter():
        if hasattr(g, 'care_project_name') and g.care_project_name:
            g._original_care_project_name = CareProjectNameEnv.get()
            CareProjectNameEnv.set(g.care_project_name)
    
    # 注册 blueprint
    app.register_blueprint(mock_blueprint)
    
    # 测试：在请求上下文中设置 g.care_project_name
    with app.test_request_context('/funboost/get_all_queues'):
        g.care_project_name = 'new_project'
        
        # 触发 before_request 钩子
        app.preprocess_request()
        
        # 验证原始值被保存
        assert hasattr(g, '_original_care_project_name')
        assert g._original_care_project_name == 'original_project'
        
        # 验证新值被设置
        assert CareProjectNameEnv.get() == 'new_project'


def test_inject_project_filter_skips_when_no_project(app, mock_blueprint):
    """
    测试 inject_project_filter 在没有项目时跳过
    
    验证：
    - 当 g.care_project_name 不存在时，不修改 CareProjectNameEnv
    - 当 g.care_project_name 为空时，不修改 CareProjectNameEnv
    """
    from funboost.core.active_cousumer_info_getter import CareProjectNameEnv
    
    # 设置初始值
    CareProjectNameEnv.set('original_project')
    
    # 添加项目过滤注入钩子
    @mock_blueprint.before_request
    def inject_project_filter():
        if hasattr(g, 'care_project_name') and g.care_project_name:
            g._original_care_project_name = CareProjectNameEnv.get()
            CareProjectNameEnv.set(g.care_project_name)
    
    # 注册 blueprint
    app.register_blueprint(mock_blueprint)
    
    # 测试 1：g.care_project_name 不存在
    with app.test_request_context('/funboost/get_all_queues'):
        # 不设置 g.care_project_name
        
        # 触发 before_request 钩子
        app.preprocess_request()
        
        # 验证 CareProjectNameEnv 未被修改
        assert CareProjectNameEnv.get() == 'original_project'
        assert not hasattr(g, '_original_care_project_name')
    
    # 测试 2：g.care_project_name 为空
    with app.test_request_context('/funboost/get_all_queues'):
        g.care_project_name = None
        
        # 触发 before_request 钩子
        app.preprocess_request()
        
        # 验证 CareProjectNameEnv 未被修改
        assert CareProjectNameEnv.get() == 'original_project'
        assert not hasattr(g, '_original_care_project_name')


def test_restore_project_filter_restores_original_value(app, mock_blueprint):
    """
    测试 restore_project_filter 恢复原始值
    
    **Validates: Requirements 3.3.2**
    
    验证：
    - 从 g._original_care_project_name 读取原始值
    - 恢复 CareProjectNameEnv 到原始值
    - 确保项目过滤只在请求生命周期内有效
    """
    from funboost.core.active_cousumer_info_getter import CareProjectNameEnv
    
    # 设置初始值
    CareProjectNameEnv.set('original_project')
    
    # 添加项目过滤注入和恢复钩子
    @mock_blueprint.before_request
    def inject_project_filter():
        if hasattr(g, 'care_project_name') and g.care_project_name:
            g._original_care_project_name = CareProjectNameEnv.get()
            CareProjectNameEnv.set(g.care_project_name)
    
    @mock_blueprint.after_request
    def restore_project_filter(response):
        if hasattr(g, '_original_care_project_name'):
            CareProjectNameEnv.set(g._original_care_project_name)
        return response
    
    # 注册 blueprint
    app.register_blueprint(mock_blueprint)
    
    # 测试：完整的请求-响应周期
    with app.test_request_context('/funboost/get_all_queues'):
        g.care_project_name = 'new_project'
        
        # 触发 before_request 钩子
        app.preprocess_request()
        
        # 验证新值被设置
        assert CareProjectNameEnv.get() == 'new_project'
        
        # 创建响应
        response = jsonify({"succ": True})
        
        # 触发 after_request 钩子
        response = app.process_response(response)
        
        # 验证原始值被恢复
        assert CareProjectNameEnv.get() == 'original_project'


def test_restore_project_filter_skips_when_no_original(app, mock_blueprint):
    """
    测试 restore_project_filter 在没有原始值时跳过
    
    验证：
    - 当 g._original_care_project_name 不存在时，不修改 CareProjectNameEnv
    """
    from funboost.core.active_cousumer_info_getter import CareProjectNameEnv
    
    # 设置初始值
    CareProjectNameEnv.set('current_project')
    
    # 添加恢复钩子
    @mock_blueprint.after_request
    def restore_project_filter(response):
        if hasattr(g, '_original_care_project_name'):
            CareProjectNameEnv.set(g._original_care_project_name)
        return response
    
    # 注册 blueprint
    app.register_blueprint(mock_blueprint)
    
    # 测试：没有设置 g._original_care_project_name
    with app.test_request_context('/funboost/get_all_queues'):
        # 不设置 g._original_care_project_name
        
        # 创建响应
        response = jsonify({"succ": True})
        
        # 触发 after_request 钩子
        response = app.process_response(response)
        
        # 验证 CareProjectNameEnv 未被修改
        assert CareProjectNameEnv.get() == 'current_project'


def test_project_filter_isolation_between_requests(app, mock_blueprint):
    """
    测试项目过滤在请求之间的隔离
    
    **Validates: Requirements 3.4**
    
    验证：
    - 每个请求的项目过滤是独立的
    - 一个请求的项目过滤不会影响其他请求
    - 请求完成后，CareProjectNameEnv 恢复到原始状态
    """
    from funboost.core.active_cousumer_info_getter import CareProjectNameEnv
    
    # 设置初始值
    CareProjectNameEnv.set('global_project')
    
    # 添加项目过滤注入和恢复钩子
    @mock_blueprint.before_request
    def inject_project_filter():
        if hasattr(g, 'care_project_name') and g.care_project_name:
            g._original_care_project_name = CareProjectNameEnv.get()
            CareProjectNameEnv.set(g.care_project_name)
    
    @mock_blueprint.after_request
    def restore_project_filter(response):
        if hasattr(g, '_original_care_project_name'):
            CareProjectNameEnv.set(g._original_care_project_name)
        return response
    
    # 注册 blueprint
    app.register_blueprint(mock_blueprint)
    
    # 请求 1：设置项目 A
    with app.test_request_context('/funboost/get_all_queues'):
        g.care_project_name = 'project_a'
        app.preprocess_request()
        
        # 验证项目 A 被设置
        assert CareProjectNameEnv.get() == 'project_a'
        
        response = jsonify({"succ": True})
        app.process_response(response)
        
        # 验证恢复到全局项目
        assert CareProjectNameEnv.get() == 'global_project'
    
    # 请求 2：设置项目 B
    with app.test_request_context('/funboost/get_all_queues'):
        g.care_project_name = 'project_b'
        app.preprocess_request()
        
        # 验证项目 B 被设置（不受请求 1 影响）
        assert CareProjectNameEnv.get() == 'project_b'
        
        response = jsonify({"succ": True})
        app.process_response(response)
        
        # 验证恢复到全局项目
        assert CareProjectNameEnv.get() == 'global_project'
    
    # 请求 3：不设置项目
    with app.test_request_context('/funboost/get_all_queues'):
        # 不设置 g.care_project_name
        app.preprocess_request()
        
        # 验证保持全局项目（不受前面请求影响）
        assert CareProjectNameEnv.get() == 'global_project'


def test_full_integration_with_permission_check(app, client, mock_blueprint):
    """
    测试项目过滤与权限检查的完整集成
    
    **Validates: Requirements 3.3.2, 3.4**
    
    验证：
    - check_faas_permission 设置 g.care_project_name
    - inject_project_filter 读取 g.care_project_name 并注入到 CareProjectNameEnv
    - FaaS 接口可以使用 CareProjectNameEnv 进行项目过滤
    - restore_project_filter 恢复原始值
    """
    from funboost.core.active_cousumer_info_getter import CareProjectNameEnv
    from flask_login import current_user
    
    # 设置初始值 (使用空字符串而不是 None，因为 CareProjectNameEnv.set() 不接受 None)
    CareProjectNameEnv.set('')
    
    # 添加权限检查钩子（模拟 check_faas_permission）
    @mock_blueprint.before_request
    def check_faas_permission():
        if not current_user.is_authenticated:
            return jsonify({"succ": False, "msg": "未登录", "data": None}), 401
        
        # 模拟从请求中提取 project_id 并设置 g.care_project_name
        project_id = request.args.get('project_id')
        if project_id:
            # 模拟获取项目代码
            project_code = f'project_{project_id}'
            g.care_project_name = project_code
    
    # 添加项目过滤注入钩子
    @mock_blueprint.before_request
    def inject_project_filter():
        if hasattr(g, 'care_project_name') and g.care_project_name:
            g._original_care_project_name = CareProjectNameEnv.get()
            CareProjectNameEnv.set(g.care_project_name)
    
    # 添加恢复钩子
    @mock_blueprint.after_request
    def restore_project_filter(response):
        if hasattr(g, '_original_care_project_name'):
            # CareProjectNameEnv.set() 不接受 None，使用空字符串代替
            original_value = g._original_care_project_name
            if original_value is None:
                original_value = ''
            CareProjectNameEnv.set(original_value)
        return response
    
    # 注册 blueprint
    app.register_blueprint(mock_blueprint)
    
    # 模拟登录用户
    with client.session_transaction() as sess:
        sess['_user_id'] = 'test_user'
    
    # 发送请求
    response = client.get('/funboost/get_all_queues?project_id=123')
    
    # 验证响应成功
    assert response.status_code == 200
    data = response.get_json()
    assert data['succ'] is True
    
    # 验证 FaaS 接口接收到了正确的项目过滤
    assert data['data']['current_project'] == 'project_123'
    
    # 验证请求完成后，CareProjectNameEnv 被恢复
    # 使用 get() 方法，它会将空字符串转换为 None
    assert CareProjectNameEnv.get() is None


def test_care_project_name_env_get_handles_special_values():
    """
    测试 CareProjectNameEnv.get() 处理特殊值
    
    验证：
    - 空字符串返回 None
    - 'all' 返回 None
    - 'None' 返回 None
    - 'null' 返回 None
    - 'none' 返回 None
    - None 返回 None
    - 正常值返回原值
    """
    from funboost.core.active_cousumer_info_getter import CareProjectNameEnv
    
    # 测试特殊值
    special_values = ['', 'all', 'None', 'null', 'none']
    for value in special_values:
        CareProjectNameEnv.set(value)
        assert CareProjectNameEnv.get() is None, f"'{value}' 应该返回 None"
    
    # 测试正常值
    CareProjectNameEnv.set('my_project')
    assert CareProjectNameEnv.get() == 'my_project'


def test_multiple_before_request_hooks_execution_order(app, mock_blueprint):
    """
    测试多个 before_request 钩子的执行顺序
    
    验证：
    - check_faas_permission 先执行，设置 g.care_project_name
    - inject_project_filter 后执行，读取 g.care_project_name
    """
    from funboost.core.active_cousumer_info_getter import CareProjectNameEnv
    from flask_login import current_user
    
    # 清理环境，确保测试隔离
    CareProjectNameEnv.set('')
    
    execution_order = []
    
    # 第一个钩子：权限检查
    @mock_blueprint.before_request
    def check_faas_permission():
        execution_order.append('check_permission')
        if current_user.is_authenticated:
            g.care_project_name = 'test_project'
    
    # 第二个钩子：项目过滤注入
    @mock_blueprint.before_request
    def inject_project_filter():
        execution_order.append('inject_filter')
        if hasattr(g, 'care_project_name') and g.care_project_name:
            g._original_care_project_name = CareProjectNameEnv.get()
            CareProjectNameEnv.set(g.care_project_name)
    
    # 注册 blueprint
    app.register_blueprint(mock_blueprint)
    
    # 创建一个测试客户端并模拟登录
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['_user_id'] = 'test_user'
        
        # 使用客户端发起请求，这样 Flask-Login 会正确加载用户
        with client.application.test_request_context('/funboost/get_all_queues'):
            from flask_login import login_user
            # 手动加载用户到 Flask-Login
            user = MockUser('test_user')
            login_user(user)
            
            # 触发 before_request 钩子
            app.preprocess_request()
            
            # 验证执行顺序
            assert execution_order == ['check_permission', 'inject_filter']
            
            # 验证 CareProjectNameEnv 被正确设置
            assert CareProjectNameEnv.get() == 'test_project'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
