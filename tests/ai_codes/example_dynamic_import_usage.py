"""
演示 funboost.faas 动态导入机制的使用示例

场景：
1. 只使用 FastAPI 的项目不需要安装 Flask 或 Django
2. 只使用 Flask 的项目不需要安装 FastAPI 或 Django
3. 想用哪个就导入哪个，互不影响
"""

# 示例 1: 只使用 FastAPI
def example_fastapi_only():
    """只使用 FastAPI 的情况"""
    print("=" * 60)
    print("示例 1: 只使用 FastAPI")
    print("=" * 60)
    
    from fastapi import FastAPI
    from funboost.faas import fastapi_router
    
    app = FastAPI()
    app.include_router(fastapi_router)
    
    print("✅ FastAPI app 创建成功，已包含 funboost_router")
    print(f"   Routes: {[route.path for route in app.routes]}")
    return app


# 示例 2: 只使用 Flask
def example_flask_only():
    """只使用 Flask 的情况"""
    print("\n" + "=" * 60)
    print("示例 2: 只使用 Flask")
    print("=" * 60)
    
    try:
        from flask import Flask
        from funboost.faas import flask_blueprint
        
        app = Flask(__name__)
        app.register_blueprint(flask_blueprint)
        
        print("✅ Flask app 创建成功，已注册 flask_blueprint")
        print(f"   Blueprints: {list(app.blueprints.keys())}")
        return app
    except ImportError as e:
        print(f"⚠️  Flask 未安装: {e}")
        return None


# 示例 3: 只使用 Django
def example_django_only():
    """只使用 Django 的情况"""
    print("\n" + "=" * 60)
    print("示例 3: 只使用 Django-Ninja")
    print("=" * 60)
    
    try:
        from ninja import NinjaAPI
        from funboost.faas import django_router
        
        api = NinjaAPI()
        api.add_router("/funboost", django_router)
        
        print("✅ Django NinjaAPI 创建成功，已添加 django_router")
        return api
    except ImportError as e:
        print(f"⚠️  Django-Ninja 未安装: {e}")
        return None


# 示例 4: 动态选择
def example_dynamic_selection(framework: str):
    """根据配置动态选择框架"""
    print("\n" + "=" * 60)
    print(f"示例 4: 动态选择框架 - {framework}")
    print("=" * 60)
    
    if framework == "fastapi":
        try:
            from funboost.faas import fastapi_router
            print(f"✅ 成功导入 {framework} router")
            return fastapi_router
        except ImportError as e:
            print(f"❌ 导入失败: {e}")
    
    elif framework == "flask":
        try:
            from funboost.faas import flask_blueprint
            print(f"✅ 成功导入 {framework} blueprint")
            return flask_blueprint
        except ImportError as e:
            print(f"❌ 导入失败: {e}")
    
    elif framework == "django":
        try:
            from funboost.faas import django_router
            print(f"✅ 成功导入 {framework} router")
            return django_router
        except ImportError as e:
            print(f"❌ 导入失败: {e}")
    
    else:
        print(f"⚠️  未知框架: {framework}")
        return None


if __name__ == "__main__":
    print("Funboost FAAS 动态导入机制演示\n")
    
    # 运行示例
    fastapi_app = example_fastapi_only()
    flask_app = example_flask_only()
    django_api = example_django_only()
    
    # 动态选择示例
    dynamic_router = example_dynamic_selection("fastapi")
    
    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    print("""
优势：
1. ✅ 按需导入：只导入实际使用的框架适配器
2. ✅ 友好提示：缺少依赖时给出清晰的安装提示
3. ✅ 零侵入性：不影响现有代码，完全向后兼容
4. ✅ IDE 支持：通过 TYPE_CHECKING 保持代码提示和类型检查

使用方法：
    from funboost.faas import fastapi_router     # 只需要 fastapi
    from funboost.faas import flask_blueprint    # 只需要 flask
    from funboost.faas import django_router      # 只需要 django-ninja
    """)
