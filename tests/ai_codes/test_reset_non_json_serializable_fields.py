"""
测试 _reset_non_json_serializable_fields 方法是否正确处理各种类型
"""
import sys
sys.path.insert(0, r'D:\codes\funboost')

from funboost.core.active_cousumer_info_getter import SingleQueueConusmerParamsGetter
from funboost.core.func_params_model import BoosterParams

# 模拟从 Redis 取出的 booster_params
test_booster_params = {
    'queue_name': 'test_queue',
    'broker_kind': 'REDIS',
    'concurrent_mode': 'threading',
    'concurrent_num': 50,
    'delay_task_apscheduler_jobstores_kind': 'redis',  # Literal 类型，不应该被重置
    'qps': None,
    'log_level': 10,
    'is_send_consumer_heartbeat_to_redis': 'True',  # 字符串形式的布尔值
    'specify_concurrent_pool': '<FunboostBaseConcurrentPool object>',  # 应该被重置为 None
    'specify_async_loop': '<asyncio.AbstractEventLoop object>',  # 应该被重置为 None
    'consuming_function_decorator': '<function decorator>',  # 应该被重置为 None
    'user_custom_record_process_info_func': '<function custom_func>',  # 应该被重置为 None
    'consumer_override_cls': '<class ConsumerOverride>',  # 应该被重置为 None
    'publisher_override_cls': '<class PublisherOverride>',  # 应该被重置为 None
}

print("原始 booster_params:")
for k, v in test_booster_params.items():
    print(f"  {k}: {v}")

# 调用重置方法
SingleQueueConusmerParamsGetter._reset_non_json_serializable_fields(test_booster_params)

print("\n重置后 booster_params:")
for k, v in test_booster_params.items():
    print(f"  {k}: {v}")

# 验证关键字段
print("\n=== 验证结果 ===")
assert test_booster_params['delay_task_apscheduler_jobstores_kind'] == 'redis', "❌ Literal 类型被错误重置!"
print("✅ delay_task_apscheduler_jobstores_kind 保持原值 'redis'")

assert test_booster_params['specify_concurrent_pool'] is None, "❌ specify_concurrent_pool 未被重置!"
print("✅ specify_concurrent_pool 被正确重置为 None")

assert test_booster_params['specify_async_loop'] is None, "❌ specify_async_loop 未被重置!"
print("✅ specify_async_loop 被正确重置为 None")

assert test_booster_params['consuming_function_decorator'] is None, "❌ consuming_function_decorator 未被重置!"
print("✅ consuming_function_decorator 被正确重置为 None")

print("\n✅ 所有测试通过!")
