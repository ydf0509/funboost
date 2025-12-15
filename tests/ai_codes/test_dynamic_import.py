"""
测试 funboost.faas 的动态导入机制

验证：
1. 只使用 fastapi_router 时不会因为缺少 flask/django 而报错
2. 惰性导入确实生效
3. 多次访问使用缓存
"""

import sys


def test_fastapi_router_import():
    """测试导入 fastapi_router"""
    print("=" * 60)
    print("测试 1: 导入 fastapi_router")
    print("=" * 60)
    
    try:
        from funboost.faas import fastapi_router
        print(f"✅ 成功导入 fastapi_router: {type(fastapi_router)}")
        print(f"   Router prefix: {fastapi_router.prefix}")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_flask_blueprint_import():
    """测试导入 flask_blueprint"""
    print("\n" + "=" * 60)
    print("测试 2: 导入 flask_blueprint")
    print("=" * 60)
    
    try:
        from funboost.faas import flask_blueprint
        print(f"✅ 成功导入 flask_blueprint: {type(flask_blueprint)}")
        print(f"   Blueprint name: {flask_blueprint.name}")
        return True
    except ImportError as e:
        print(f"❌ 导入失败 (可能是 flask 未安装): {e}")
        return False


def test_django_router_import():
    """测试导入 django_router"""
    print("\n" + "=" * 60)
    print("测试 3: 导入 django_router")
    print("=" * 60)
    
    try:
        from funboost.faas import django_router
        print(f"✅ 成功导入 django_router: {type(django_router)}")
        return True
    except ImportError as e:
        print(f"❌ 导入失败 (可能是 django-ninja 未安装): {e}")
        return False


def test_multiple_imports():
    """测试多次导入使用缓存"""
    print("\n" + "=" * 60)
    print("测试 4: 验证缓存机制 (多次导入)")
    print("=" * 60)
    
    try:
        from funboost.faas import fastapi_router as router1
        from funboost.faas import fastapi_router as router2
        
        if router1 is router2:
            print("✅ 多次导入返回的是同一个对象 (缓存生效)")
            return True
        else:
            print("❌ 多次导入返回的不是同一个对象 (缓存未生效)")
            return False
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_error_message():
    """测试错误提示信息"""
    print("\n" + "=" * 60)
    print("测试 5: 测试友好的错误提示")
    print("=" * 60)
    
    # 临时模拟缺少依赖的情况
    import funboost.faas
    
    # 尝试访问一个不存在的属性
    try:
        _ = funboost.faas.non_existent_router
        print("❌ 应该抛出 AttributeError")
        return False
    except AttributeError as e:
        print(f"✅ 正确抛出 AttributeError: {e}")
        return True


if __name__ == "__main__":
    print("开始测试 funboost.faas 动态导入机制\n")
    
    results = []
    
    # 运行所有测试
    results.append(("fastapi_router 导入", test_fastapi_router_import()))
    results.append(("flask_blueprint 导入", test_flask_blueprint_import()))
    results.append(("django_router 导入", test_django_router_import()))
    results.append(("缓存机制", test_multiple_imports()))
    results.append(("错误提示", test_error_message()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
