import sys
import os
import pprint
import typing
# 确保 funboost 在 path 中
sys.path.insert(0, r'D:\codes\funboost')

from funboost.core.func_params_model import BoosterParams, FunctionResultStatusPersistanceConfig
from funboost.core.active_cousumer_info_getter import SingleQueueConusmerParamsGetter
from funboost.concurrent_pool.base_pool_type import FunboostBaseConcurrentPool
from funboost.core.pydantic_compatible_base import get_cant_json_serializable_fields

# 1. 定义测试用 Mock 类
class MyPool(FunboostBaseConcurrentPool):
    def __init__(self, n):
        self.n = n
    
    def submit(self, func, *args, **kwargs):
        pass
        
    def shutdown(self, wait=True):
        pass

def my_decorator(f):
    return f

class MyConsumerCls:
    pass

class MyPublisherCls:
    pass

def demo():
    print("=== BoosterParams 序列化与反序列化重置演示 ===\n")
    
    print(get_cant_json_serializable_fields(BoosterParams))
    
    # 2. 创建带有各种不可序列化对象的 BoosterParams
    print("1. 创建原始 BoosterParams 对象...")
    bp_original = BoosterParams(
        queue_name="demo_queue_serialization_test",
        # 传入不可序列化对象
        specify_concurrent_pool=MyPool(10),
        consuming_function_decorator=my_decorator,
        consumer_override_cls=MyConsumerCls,
        publisher_override_cls=MyPublisherCls,
        # 传入特殊类型但可序列化的字段
        delay_task_apscheduler_jobstores_kind='memory',
        retry_interval=5.0
    )
    
    print(f"   [原始] specify_concurrent_pool 类型: {type(bp_original.specify_concurrent_pool)}")
    print(f"   [原始] consuming_function_decorator 类型: {type(bp_original.consuming_function_decorator)}")
    
    # 3. 模拟存入 Redis：转换为字符串字典 (get_str_dict)
    # 这是 BaseJsonAbleModel 的特性，将不可 json 序列化的对象转为 str
    print("\n2. 模拟序列化 (get_str_dict) - 即存入 Redis 的格式...")
    redis_data = bp_original.get_str_dict()
    
    # 展示 Redis 中的数据样子
    print("   [Redis数据] 部分关键字段值:")
    keys_to_show = [
        'specify_concurrent_pool', 
        'consuming_function_decorator',
        'consumer_override_cls',
        'delay_task_apscheduler_jobstores_kind'
    ]
    for k in keys_to_show:
        print(f"     {k}: {redis_data.get(k)} (类型: {type(redis_data.get(k)).__name__})")
        
    # 验证确实变成了字符串
    pool_str = redis_data['specify_concurrent_pool']
    print(f"     -> specify_concurrent_pool str value: {pool_str}")
    assert isinstance(pool_str, str)
    assert 'MyPool' in pool_str

    # 4. 模拟从 Redis 取出并执行自动清理
    print("\n3. 执行 _reset_non_json_serializable_fields 自动清理...")
    
    # 调用静态方法清理
    SingleQueueConusmerParamsGetter._reset_non_json_serializable_fields(redis_data)
    
    redis_data['function_result_status_persistance_conf'] = FunctionResultStatusPersistanceConfig(
        is_save_status=False,is_save_result=False)
    print("   [清理后] 关键字段值:")
    for k in keys_to_show:
        val = redis_data.get(k)
        print(f"     {k}: {val}")

    # 5. 验证清理结果
    print("\n4. 验证清理逻辑正确性...")
    
    # 应该被重置为 None 的字段
    assert redis_data['specify_concurrent_pool'] is None, "❌ specify_concurrent_pool 未重置为 None"
    assert redis_data['consuming_function_decorator'] is None, "❌ consuming_function_decorator 未重置为 None"
    assert redis_data['consumer_override_cls'] is None, "❌ consumer_override_cls 未重置为 None"
    
    # 应该保留原值的字段
    assert redis_data['delay_task_apscheduler_jobstores_kind'] == 'memory', "❌ delay_task_apscheduler_jobstores_kind 被错误重置"
    
    print("   ✅ 所有的断言检查通过！")
    
    # 6. 验证重新实例化
    print("\n5. 尝试用清理后的数据重新实例化 BoosterParams...")
    try:
        bp_new = BoosterParams(**redis_data)
        print("   ✅ 重新实例化成功！")
        print(f"   [新对象] specify_concurrent_pool: {bp_new.specify_concurrent_pool}")
        print(f"   [新对象] delay_task_apscheduler_jobstores_kind: {bp_new.delay_task_apscheduler_jobstores_kind}")
    except Exception as e:
        print(f"   ❌ 重新实例化失败: {e}")
        raise

if __name__ == '__main__':
    demo()
