"""
测试 get_all_queues 接口的示例代码

这个文件展示如何使用新增的 /funboost/get_all_queues 接口
"""

import requests

# 测试 Flask 版本
def test_flask_get_all_queues():
    """测试 Flask 版本的 get_all_queues 接口"""
    url = "http://127.0.0.1:5000/funboost/get_all_queues"
    
    try:
        response = requests.get(url)
        result = response.json()
        
        print("=" * 50)
        print("Flask 接口测试结果:")
        print(f"成功: {result['succ']}")
        print(f"消息: {result['msg']}")
        if result.get('data'):
            print(f"队列总数: {result['data']['count']}")
            print(f"队列列表: {result['data']['queues']}")
        print("=" * 50)
        
        return result
    except Exception as e:
        print(f"请求失败: {e}")
        return None


# 测试 FastAPI 版本
def test_fastapi_get_all_queues():
    """测试 FastAPI 版本的 get_all_queues 接口"""
    url = "http://127.0.0.1:16666/funboost/get_all_queues"
    
    try:
        response = requests.get(url)
        result = response.json()
        
        print("=" * 50)
        print("FastAPI 接口测试结果:")
        print(f"成功: {result['succ']}")
        print(f"消息: {result['msg']}")
        if result.get('data'):
            print(f"队列总数: {result['data']['count']}")
            print(f"队列列表: {result['data']['queues']}")
        print("=" * 50)
        
        return result
    except Exception as e:
        print(f"请求失败: {e}")
        return None


# 测试 Django Ninja 版本
def test_django_ninja_get_all_queues():
    """测试 Django Ninja 版本的 get_all_queues 接口"""
    url = "http://127.0.0.1:8000/api/funboost/get_all_queues"
    
    try:
        response = requests.get(url)
        result = response.json()
        
        print("=" * 50)
        print("Django Ninja 接口测试结果:")
        print(f"成功: {result['succ']}")
        print(f"消息: {result['msg']}")
        if result.get('data'):
            print(f"队列总数: {result['data']['count']}")
            print(f"队列列表: {result['data']['queues']}")
        print("=" * 50)
        
        return result
    except Exception as e:
        print(f"请求失败: {e}")
        return None


if __name__ == "__main__":
    print("开始测试 get_all_queues 接口...")
    print("\n请确保已经启动了对应的 Web 服务\n")
    
    # 测试 Flask 版本
    print("测试 Flask 版本 (端口 5000):")
    test_flask_get_all_queues()
    
    print("\n")
    
    # 测试 FastAPI 版本
    print("测试 FastAPI 版本 (端口 16666):")
    test_fastapi_get_all_queues()
    
    print("\n")
    
    # 测试 Django Ninja 版本
    print("测试 Django Ninja 版本 (端口 8000):")
    test_django_ninja_get_all_queues()
