"""
funboost.faas FastAPI Router 接口测试示例

本示例演示如何使用 funboost.faas 提供个接口：

1. test_publish_and_get_result - 演示发布消息并等待结果（RPC模式）
2. test_get_msg_count - 演示获取队列消息数量
3. test_publish_async_then_get_result - 演示异步发布，先获取task_id，再根据task_id获取结果
4. test_get_all_queues - 演示获取所有已注册的队列名称

"""

import requests
import time
import json

base_url = "http://127.0.0.1:8000"

def test_publish_and_get_result():
    """测试发布消息并等待结果（RPC模式）

    接口有对queue_name是否存在的校验，支持校验消息内容是否正确。所以不用担心跨部门用户使用了错误的queue_name，或者消息内容不正确。
    用户可以先通过 /get_queues_config 接口获取所有队列的配置信息，就知道有哪些队列，以及每个队列的消费函数支持的消息内容需要包括哪些入参字段了。
    """
    print("=" * 60)
    print("1. Testing publish and get result (RPC mode)...")
    print("=" * 60)
    
    url = f"{base_url}/funboost/publish"
    data = {
        "queue_name": "test_funboost_faas_queue",
        "msg_body": {"x": 10, "y": 20},
        "need_result": True,
        "timeout": 10
    }
    # publish 
    try:
        resp = requests.post(url, json=data)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")
        
        if resp.status_code == 200:
            result_data = resp.json()
            if result_data['succ']:
                # 新格式：数据在 data 字段中
                task_id = result_data['data']['task_id']
                status_and_result = result_data['data']['status_and_result']
                print(f"\n✅ Success!")
                print(f"Task ID: {task_id}")
                print(f"Result: {status_and_result}")
            else:
                print(f"\n❌ Failed: {result_data['msg']}")
    except Exception as e:
        print(f"\n❌ Request failed: {e}")

def test_get_msg_count():
    """测试获取队列消息数量"""
    print("\n" + "=" * 60)
    print("2. Testing get message count...")
    print("=" * 60)
    
    url = f"{base_url}/funboost/get_msg_count"
    params = {"queue_name": "test_funboost_faas_queue"}
    
    try:
        resp = requests.get(url, params=params)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")
        
        if resp.status_code == 200:
            result_data = resp.json()
            if result_data['succ']:
                # 新格式：数据在 data 字段中
                queue_name = result_data['data']['queue_name']
                count = result_data['data']['count']
                print(f"\n✅ Success!")
                print(f"Queue: {queue_name}")
                print(f"Message Count: {count}")
            else:
                print(f"\n❌ Failed: {result_data['msg']}")
    except Exception as e:
        print(f"\n❌ Request failed: {e}")

def test_publish_async_then_get_result():
    """测试异步发布，先获取task_id，再根据task_id获取结果"""
    print("\n" + "=" * 60)
    print("3. Testing publish async then get result by task_id...")
    print("=" * 60)
    
    # 步骤1: 发布消息（不等待结果）
    url_pub = f"{base_url}/funboost/publish"
    data = {
        "queue_name": "test_funboost_faas_queue",
        "msg_body": {"x": 33, "y": 44},
        "need_result": False,  # 不等待结果，立即返回
    }
    
    try:
        resp = requests.post(url_pub, json=data)
        print(f"Publish Status Code: {resp.status_code}")
        print(f"Publish Response: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")
        
        if resp.status_code == 200:
            result_data = resp.json()
            if result_data['succ']:
                # 新格式：数据在 data 字段中
                task_id = result_data['data']['task_id']
                print(f"\n✅ Message published!")
                print(f"Task ID: {task_id}")
                
                if task_id:
                    # 步骤2: 根据task_id获取结果
                    print("\nWaiting for task to complete...")
                    time.sleep(0.2)  # 等待一小段时间让任务完成
                    
                    url_get = f"{base_url}/funboost/get_result"
                    params = {"task_id": task_id, "timeout": 5}
                    resp_get = requests.get(url_get, params=params)
                    
                    print(f"\nGet Result Status Code: {resp_get.status_code}")
                    print(f"Get Result Response: {json.dumps(resp_get.json(), indent=2, ensure_ascii=False)}")
                    
                    if resp_get.status_code == 200:
                        get_result_data = resp_get.json()
                        if get_result_data['succ']:
                            # 新格式：数据在 data 字段中
                            status_and_result = get_result_data['data']['status_and_result']
                            print(f"\n✅ Got result!")
                            print(f"Result: {status_and_result}")
                        else:
                            print(f"\n⚠️  {get_result_data['msg']}")
            else:
                print(f"\n❌ Publish failed: {result_data['msg']}")
    except Exception as e:
        print(f"\n❌ Request failed: {e}")

def test_get_all_queues():
    """测试获取所有已注册的队列名称"""
    print("\n" + "=" * 60)
    print("4. Testing get all queues...")
    print("=" * 60)
    
    url = f"{base_url}/funboost/get_all_queues"
    
    try:
        resp = requests.get(url)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")
        
        if resp.status_code == 200:
            result_data = resp.json()
            if result_data['succ']:
                # 新格式：数据在 data 字段中
                queues = result_data['data']['queues']
                count = result_data['data']['count']
                print(f"\n✅ Success!")
                print(f"Total Queues: {count}")
                print(f"Queue List:")
                for i, queue in enumerate(queues, 1):
                    print(f"  {i}. {queue}")
            else:
                print(f"\n❌ Failed: {result_data['msg']}")
    except Exception as e:
        print(f"\n❌ Request failed: {e}")

if __name__ == "__main__":
    print("\n" + "🚀 " * 20)
    print("FastAPI Funboost faas  接口测试")
    print("🚀 " * 20)
    
    # 测试所有4个接口
    test_publish_and_get_result()
    test_get_msg_count()
    test_publish_async_then_get_result()
    test_get_all_queues()
    
    print("\n" + "✅ " * 20)
    print("测试完成！")
    print("✅ " * 20 + "\n")
