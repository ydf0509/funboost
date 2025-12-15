# -*- coding: utf-8 -*-
"""
测试 Flask 定时任务接口
测试添加、查询、暂停、恢复、删除定时任务
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Flask 服务地址
BASE_URL = "http://localhost:27019"

def test_add_timing_job_date():
    """测试添加一次性任务（date 触发器）"""
    print("\n" + "="*60)
    print("测试1: 添加一次性任务 (date)")
    print("="*60)
    
    # 设置5秒后执行
    run_date = (datetime.now() + timedelta(seconds=5)).strftime('%Y-%m-%d %H:%M:%S')
    
    data = {
        "queue_name": "test_funboost_task3",
        "trigger": "date",
        "job_id": "date_job_test_001",
        "job_store_kind": "redis",
        "replace_existing": True,
        "run_date": run_date,
        "kwargs": {
            "user_id": 123,
            "name": "张三",
            "action": "一次性任务测试"
        }
    }
    
    print(f"请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    response = requests.post(
        f"{BASE_URL}/funboost/add_timing_job",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"响应状态: {response.status_code}")
    print(f"响应数据: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()


def test_add_timing_job_interval():
    """测试添加间隔执行任务（interval 触发器）"""
    print("\n" + "="*60)
    print("测试2: 添加间隔执行任务 (interval)")
    print("="*60)
    
    data = {
        "queue_name": "test_funboost_faas_queue",
        "trigger": "interval",
        "job_id": "interval_job_test_001",
        "job_store_kind": "redis",
        "replace_existing": True,
        "seconds": 10,  # 每10秒执行一次
        "kwargs": {
            # "user_id": 456,
            # "name": "李四",
            # "action": "间隔任务测试"
            "x":8,"y":9
        }
    }
    
    print(f"请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    response = requests.post(
        f"{BASE_URL}/funboost/add_timing_job",
        json=data
    )
    
    print(f"响应状态: {response.status_code}")
    print(f"响应数据: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()


def test_add_timing_job_cron():
    """测试添加定时任务（cron 触发器）"""
    print("\n" + "="*60)
    print("测试3: 添加定时任务 (cron)")
    print("="*60)
    
    data = {
        "queue_name": "test_funboost_task3",
        "trigger": "cron",
        "job_id": "cron_job_test_001",
        "job_store_kind": "redis",
        "replace_existing": True,
        "hour": "*/1",  # 每小时执行一次
        "minute": "0",
        "second": "0",
        "kwargs": {
            "user_id": 789,
            "name": "王五",
            "action": "Cron任务测试",
            "tags": ["定时", "重要"]
        }
    }
    
    print(f"请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    response = requests.post(
        f"{BASE_URL}/funboost/add_timing_job",
        json=data
    )
    
    print(f"响应状态: {response.status_code}")
    print(f"响应数据: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()


def test_get_timing_jobs(queue_name=None):
    """测试获取任务列表"""
    print("\n" + "="*60)
    print("测试4: 获取任务列表")
    print("="*60)
    
    params = {"job_store_kind": "redis"}
    if queue_name:
        params["queue_name"] = queue_name
    
    print(f"请求参数: {params}")
    
    response = requests.get(
        f"{BASE_URL}/funboost/get_timing_jobs",
        params=params
    )
    
    print(f"响应状态: {response.status_code}")
    result = response.json()
    print(f"任务数量: {len(result.get('data', {}).get('jobs', []))}")
    print(f"响应数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    return result


def test_get_timing_job(job_id, queue_name):
    """测试获取单个任务详情"""
    print("\n" + "="*60)
    print("测试5: 获取单个任务详情")
    print("="*60)
    
    params = {
        "job_id": job_id,
        "queue_name": queue_name,
        "job_store_kind": "redis"
    }
    
    print(f"请求参数: {params}")
    
    response = requests.get(
        f"{BASE_URL}/funboost/get_timing_job",
        params=params
    )
    
    print(f"响应状态: {response.status_code}")
    print(f"响应数据: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()


def test_pause_timing_job(job_id, queue_name):
    """测试暂停任务"""
    print("\n" + "="*60)
    print("测试6: 暂停任务")
    print("="*60)
    
    params = {
        "job_id": job_id,
        "queue_name": queue_name,
        "job_store_kind": "redis"
    }
    
    print(f"请求参数: {params}")
    
    response = requests.post(
        f"{BASE_URL}/funboost/pause_timing_job",
        params=params
    )
    
    print(f"响应状态: {response.status_code}")
    print(f"响应数据: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()


def test_resume_timing_job(job_id, queue_name):
    """测试恢复任务"""
    print("\n" + "="*60)
    print("测试7: 恢复任务")
    print("="*60)
    
    params = {
        "job_id": job_id,
        "queue_name": queue_name,
        "job_store_kind": "redis"
    }
    
    print(f"请求参数: {params}")
    
    response = requests.post(
        f"{BASE_URL}/funboost/resume_timing_job",
        params=params
    )
    
    print(f"响应状态: {response.status_code}")
    print(f"响应数据: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()


def test_delete_timing_job(job_id, queue_name):
    """测试删除任务"""
    print("\n" + "="*60)
    print("测试8: 删除任务")
    print("="*60)
    
    params = {
        "job_id": job_id,
        "queue_name": queue_name,
        "job_store_kind": "redis"
    }
    
    print(f"请求参数: {params}")
    
    response = requests.delete(
        f"{BASE_URL}/funboost/delete_timing_job",
        params=params
    )
    
    print(f"响应状态: {response.status_code}")
    print(f"响应数据: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()


def test_delete_all_timing_jobs(queue_name=None):
    """测试删除所有任务"""
    print("\n" + "="*60)
    print("测试9: 删除所有任务")
    print("="*60)
    
    params = {"job_store_kind": "redis"}
    if queue_name:
        params["queue_name"] = queue_name
    
    print(f"请求参数: {params}")
    
    response = requests.delete(
        f"{BASE_URL}/funboost/delete_all_timing_jobs",
        params=params
    )
    
    print(f"响应状态: {response.status_code}")
    print(f"响应数据: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()


def run_all_tests():
    """运行所有测试"""
    print("\n" + "#"*60)
    print("# 开始测试 Flask 定时任务接口")
    print("#"*60)
    
    queue_name = "test_funboost_faas_queue"
  
    
    try:
        # 1. 添加三种类型的任务
        result1 = test_add_timing_job_date()
        time.sleep(0.5)
        
        result2 = test_add_timing_job_interval()
        time.sleep(0.5)
        
        result3 = test_add_timing_job_cron()
        time.sleep(0.5)
        
        # 2. 获取所有任务
        test_get_timing_jobs()
        time.sleep(0.5)
        
        # 3. 获取指定队列的任务
        test_get_timing_jobs(queue_name)
        time.sleep(0.5)
        
        # # 4. 获取单个任务详情
        # test_get_timing_job("interval_job_test_001", queue_name)
        # time.sleep(0.5)
        
        # # 5. 暂停任务
        # test_pause_timing_job("interval_job_test_001", queue_name)
        # time.sleep(0.5)
        
        # # 6. 查看暂停后的状态
        # print("\n查看暂停后的任务列表:")
        # test_get_timing_jobs(queue_name)
        # time.sleep(0.5)
        
        # # 7. 恢复任务
        # test_resume_timing_job("interval_job_test_001", queue_name)
        # time.sleep(0.5)
        
        # # 8. 查看恢复后的状态
        # print("\n查看恢复后的任务列表:")
        # test_get_timing_jobs(queue_name)
        # time.sleep(0.5)
        
        # # 9. 删除单个任务
        # test_delete_timing_job("date_job_test_001", queue_name)
        # time.sleep(0.5)
        
        # # 10. 查看删除后的任务列表
        # print("\n查看删除单个任务后的列表:")
        # test_get_timing_jobs(queue_name)
        
        # # 11. 删除所有任务（可选，谨慎使用）
        # # test_delete_all_timing_jobs(queue_name)
        
        # print("\n" + "#"*60)
        # print("# 所有测试完成！")
        # print("#"*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # 运行所有测试
    # run_all_tests()
    
    # 或者单独运行某个测试
    test_add_timing_job_interval()
    test_get_timing_jobs("test_funboost_faas_queue")
