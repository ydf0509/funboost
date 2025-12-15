# -*- coding: utf-8 -*-
"""
诊断页面添加任务失败的问题
直接调用后端代码，模拟页面请求
"""

from funboost.core.active_cousumer_info_getter import SingleQueueConusmerParamsGetter
from funboost.timing_job.timing_push import ApsJobAdder
from funboost.utils import redis_manager
from funboost.constant import RedisKeys
import traceback

def test_add_job_directly():
    """直接调用 Python 代码添加任务"""
    print("="*60)
    print("测试1: 直接使用 Python 代码添加任务")
    print("="*60)
    
    queue_name = "test_funboost_faas_queue"
    job_id = "python_direct_test"
    
    try:
        # 获取 booster
        booster = SingleQueueConusmerParamsGetter(queue_name)\
            .generate_booster_by_funboost_redis_info_for_timing_push()
        
        # 创建 ApsJobAdder
        job_adder = ApsJobAdder(booster, job_store_kind='redis', is_auto_start=True)
        
        print(f"调度器对象: {job_adder.aps_obj}")
        print(f"调度器 ID: {id(job_adder.aps_obj)}")
        print(f"添加前任务数: {len(job_adder.aps_obj.get_jobs())}")
        
        # 添加任务
        job = job_adder.add_push_job(
            trigger='interval',
            seconds=15,
            kwargs={"test": "from_python"},
            id=job_id,
            replace_existing=True
        )
        
        print(f"\n✅ 任务添加成功:")
        print(f"   Job ID: {job.id}")
        print(f"   Trigger: {job.trigger}")
        print(f"   Next Run: {job.next_run_time}")
        
        # 立即查询
        print(f"\n添加后任务数: {len(job_adder.aps_obj.get_jobs())}")
        
        # 查看 Redis
        redis_conn = redis_manager.get_redis_connection()
        jobs_key = RedisKeys.gen_funboost_redis_apscheduler_jobs_key_by_queue_name(queue_name)
        jobs_in_redis = redis_conn.hgetall(jobs_key)
        
        print(f"\nRedis 中的任务:")
        print(f"   Jobs Key: {jobs_key}")
        print(f"   任务数: {len(jobs_in_redis)}")
        print(f"   Job IDs: {[k.decode() if isinstance(k, bytes) else k for k in jobs_in_redis.keys()]}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 添加失败: {e}")
        traceback.print_exc()
        return False


def test_add_job_via_flask_api():
    """模拟 Flask 路由的处理逻辑"""
    print("\n" + "="*60)
    print("测试2: 模拟 Flask API 的处理逻辑")
    print("="*60)
    
    # 模拟前端提交的数据
    data = {
        "queue_name": "test_funboost_faas_queue",
        "trigger": "interval",
        "job_id": "flask_simulation_test",
        "job_store_kind": "redis",
        "replace_existing": True,
        "seconds": 20,
        "kwargs": {
            "test": "from_flask_simulation"
        }
    }
    
    print(f"模拟的请求数据: {data}\n")
    
    try:
        queue_name = data.get('queue_name')
        trigger = data.get('trigger')
        job_id = data.get('job_id')
        job_store_kind = data.get('job_store_kind', 'redis')
        replace_existing = data.get('replace_existing', False)
        
        # 获取 booster
        booster = SingleQueueConusmerParamsGetter(queue_name)\
            .generate_booster_by_funboost_redis_info_for_timing_push()
        job_adder = ApsJobAdder(booster, job_store_kind=job_store_kind, is_auto_start=True)
        
        print(f"调度器对象: {job_adder.aps_obj}")
        print(f"调度器 ID: {id(job_adder.aps_obj)}")
        print(f"添加前任务数: {len(job_adder.aps_obj.get_jobs())}")
        
        # 构建触发器参数（和 flask_adapter.py 一样）
        trigger_args = {}
        
        if trigger == 'interval':
            if data.get('weeks') is not None:
                trigger_args['weeks'] = data.get('weeks')
            if data.get('days') is not None:
                trigger_args['days'] = data.get('days')
            if data.get('hours') is not None:
                trigger_args['hours'] = data.get('hours')
            if data.get('minutes') is not None:
                trigger_args['minutes'] = data.get('minutes')
            if data.get('seconds') is not None:
                trigger_args['seconds'] = data.get('seconds')
        
        print(f"\ntrigger_args: {trigger_args}")
        
        # 添加任务
        job = job_adder.add_push_job(
            trigger=trigger,
            args=data.get('args'),
            kwargs=data.get('kwargs'),
            id=job_id,
            replace_existing=replace_existing,
            **trigger_args
        )
        
        print(f"\n✅ 任务添加成功:")
        print(f"   Job ID: {job.id}")
        print(f"   Trigger: {job.trigger}")
        print(f"   Next Run: {job.next_run_time}")
        
        # 立即查询
        print(f"\n添加后任务数: {len(job_adder.aps_obj.get_jobs())}")
        
        # 查看 Redis
        redis_conn = redis_manager.get_redis_connection()
        jobs_key = RedisKeys.gen_funboost_redis_apscheduler_jobs_key_by_queue_name(queue_name)
        jobs_in_redis = redis_conn.hgetall(jobs_key)
        
        print(f"\nRedis 中的任务:")
        print(f"   Jobs Key: {jobs_key}")
        print(f"   任务数: {len(jobs_in_redis)}")
        print(f"   Job IDs: {[k.decode() if isinstance(k, bytes) else k for k in jobs_in_redis.keys()]}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 添加失败: {e}")
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # 运行测试
    result1 = test_add_job_directly()
    result2 = test_add_job_via_flask_api()
    
    print("\n" + "="*60)
    print("测试结果:")
    print(f"  测试1 (Python 直接): {'✅ 成功' if result1 else '❌ 失败'}")
    print(f"  测试2 (模拟 Flask): {'✅ 成功' if result2 else '❌ 失败'}")
    print("="*60)
