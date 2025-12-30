# -*- coding: utf-8 -*-

"""
funboost 所有用法的使用， demo 例子 演示
这个文件集中演示了 funboost 的 90% 主要功能用法。
"""

import time
import random
import asyncio
import datetime
from funboost import (
    boost,                  # 核心装饰器
    BoosterParams,          # 参数配置类
    BrokerEnum,             # 中间件枚举
    ConcurrentModeEnum,     # 并发模式枚举
    TaskOptions, # 优先级/延时配置
    ApsJobAdder,            # 定时任务添加器
    ctrl_c_recv,            # 阻塞主线程工具
    fct,                    # 上下文对象 (Funboost Current Task)
    BoostersManager,        # 消费者管理器 (用于分组启动)
    AsyncResult,            # 同步编程生态的异步结果对象
    AioAsyncResult,          # asyncio生态的异步结果对象
)

# ==========================================
# 1. 基础任务 (使用 SQLite 本地文件作为队列，无需安装 Redis/RabbitMQ 即可测试)
# ==========================================
@boost(BoosterParams(
    queue_name="demo_queue_basic",
    broker_kind=BrokerEnum.SQLITE_QUEUE,  # 使用本地 SQLite 文件作为队列
    concurrent_num=2,                     # 线程并发数量
))
def task_basic(x, y):
    print(f"[基础任务] 正在处理: {x} + {y} = {x + y}")
    time.sleep(0.5)
    return x + y


# ==========================================
# 2. 错误重试任务 (演示自动重试机制)
# 2.b 获取taskid和消息发布时间 (演示fct上下文的使用)
# ==========================================
@boost(BoosterParams(
    queue_name="demo_queue_retry",
    broker_kind=BrokerEnum.MEMORY_QUEUE,  # 使用内存队列
    max_retry_times=3,                    # 最大重试 3 次
    retry_interval=1,                     # 重试间隔 1 秒
    is_print_detail_exception=False       # 不打印详细堆栈，保持控制台整洁
))
def task_retry(n):
    # 模拟：只有 n > 8 才会成功，否则报错触发重试
    if n <= 8:
        print(f"[重试任务] 输入 {n} 模拟失败，当前是第 {fct.function_result_status.run_times} 次运行...")
        raise ValueError("模拟出错啦")
    print(f"[重试任务] 输入 {n} 成功处理！,任务id是：{fct.task_id} ,发布时间是：{fct.function_result_status.publish_time_format}")


# ==========================================
# 3. QPS 控频任务 (精准控制每秒执行次数)
# ==========================================
@boost(BoosterParams(
    queue_name="demo_queue_qps",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=2,  # 限制每秒只执行 2 次，无论并发开多大
))
def task_qps(idx):
    print(f"[QPS任务] {idx} 正在运行 (每秒约2次)... {datetime.datetime.now()}")


# ==========================================
# 4. Asyncio 协程任务 (高性能 IO 密集型)
# ==========================================
@boost(BoosterParams(
    queue_name="demo_queue_async",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_mode=ConcurrentModeEnum.ASYNC, # 开启 Asyncio 模式
    concurrent_num=100,  # 协程并发数可以设置很大
    is_using_rpc_mode = True,
))
async def task_async(url):
    print(f"[Async任务] 开始请求: {url}")
    await asyncio.sleep(1) # 模拟 IO 等待
    print(f"[Async任务] 请求结束: {url}")
    return f'url:{url} ,resp: mock_resp'


# ==========================================
# 5. RPC 任务 (发布端获取消费端结果)
# 注意：RPC模式通常需要 Redis 支持，这里使用 MEMORY_QUEUE 模拟演示(Funboost支持内存模拟)
# 但生产环境强烈建议配置 funboost_config.py 使用 Redis
# ==========================================
@boost(BoosterParams(
    queue_name="demo_queue_rpc",
    broker_kind=BrokerEnum.MEMORY_QUEUE, 
    is_using_rpc_mode=True,  # 开启 RPC 模式
    rpc_result_expire_seconds=10
))
def task_rpc(a, b):
    time.sleep(1)
    return a * b


# ==========================================
# 6. 任务过滤 (去重)
# ==========================================
@boost(BoosterParams(
    queue_name="demo_queue_filter",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    do_task_filtering=True,           # 开启过滤
    task_filtering_expire_seconds=60  # 60秒内参数相同的任务只执行一次
))
def task_filter(user_id, user_sex, user_name):
    print(f"[过滤任务] 正在执行: user_id={user_id} name={user_name} sex={user_sex}")


# ==========================================
# 7. 延时任务 (消费者取出后，延迟执行)
# ==========================================
@boost(BoosterParams(queue_name="demo_queue_delay", broker_kind=BrokerEnum.MEMORY_QUEUE))
def task_delay(msg):
    print(f"[延时任务] 终于执行了: {msg} - 当前时间: {datetime.datetime.now()}")


# ==========================================
# 10. Booster Group (分组启动演示)
# 场景：假设你有100个消费函数，只想启动其中属于 'my_group_a' 业务组的函数
# ==========================================
@boost(BoosterParams(
    queue_name="demo_group_task_1", 
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    booster_group="my_group_a"  # 指定分组名称
))
def task_group_a_1(x):
    print(f"[分组任务A-1] 处理: {x}")

@boost(BoosterParams(
    queue_name="demo_group_task_2", 
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    booster_group="my_group_a"  # 指定相同的分组名称
))
def task_group_a_2(x):
    print(f"[分组任务A-2] 处理: {x}")

@boost(BoosterParams(
    queue_name="demo_group_task_3", 
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    booster_group="my_group_b"  # 不同的分组，不会被 my_group_a 启动
))
def task_group_b_1(x):
    print(f"[分组任务B-1] (这个不应该运行，因为没有启动my_group_b分组，也没有启动task_group_b_1消费函数): {x}")


# ==========================================
# 主程序入口
# ==========================================
if __name__ == '__main__':
    # --- 1. 启动常规消费者 ---
    # 启动方式 A: 单个启动
    task_basic.consume()
    task_retry.consume()
    task_qps.consume()
    task_async.consume()
    task_rpc.consume()
    task_filter.consume()
    task_delay.consume()
    
    # 启动方式 B: 多进程启动 (用于 CPU 密集型任务，这里仅做演示)
    # task_basic.multi_process_consume(process_num=2)   # 或者 task_basic.mp_consume(process_num=2) ,mp_consume是multi_process_consume的别名简写

    # 启动方式 C: 分组启动 (新增演示)
    print(">>> 正在启动属于 'my_group_a' 分组的所有消费者...")
    BoostersManager.consume_group("my_group_a")
    # 注意：这里没有启动 task_group_b_1，因为它属于 my_group_b

    print("=== 消费者已启动，开始发布任务 ===")
    time.sleep(1)

    # --- 2. 发布基础任务 ---
    for i in range(5):
        task_basic.push(i, i+1)

    # --- 3. 发布重试任务 ---
    task_retry.push(5) # 这个会失败并重试3次
    task_retry.push(6666) # 这个会成功无需重试

    # --- 4. 发布 QPS 任务 ---
    for i in range(6):
        task_qps.push(i)
    
    # --- 5. 发布 Async 任务 ---
    for i in range(3):
        # 支持异步 push: await task_async.aio_push(...)
        task_async.push(f"http://site-{i}.com")

    # --- 6. RPC 获取结果演示 ---
    print("\n--- RPC 演示 ---")
    # push 返回的是 AsyncResult 对象
    async_result:AsyncResult = task_rpc.push(10, 20) 
    print("RPC 任务已发布，正在等待结果...")
    # result 属性会阻塞当前线程直到获取结果
    print(f"RPC 结果: {async_result.result}") 
    

    # --- 7. 任务过滤演示 ---
    print("\n--- 过滤演示 ---")
    print("如果不指定filter_str， 默认使用函数的所有入参包括 user_id user_sex user_name 来做过滤")
    task_filter.push(1001,"man",user_name="xiaomin")

    # 演示: 指定字符串过滤 (publish 方式 + task_options)
    # 场景：只根据 user_id 过滤，即使其他参数不同，只要 user_id 相同就被过滤
    print("发布 user_id=1001 (第1次)")
    task_filter.publish(
        msg={"user_id": 1001, "user_sex": "man", "user_name": "Tom"},
        task_options=TaskOptions(filter_str="1001")
    )
    
    print("发布 user_id=1001 (第2次, name不同, 但filter_str相同, 应该被过滤)")
    task_filter.publish(
        msg={"user_id": 1001, "user_sex": "man", "user_name": "Jerry"},
        task_options=TaskOptions(filter_str="1001")
    )


    # --- 8. 延时任务演示 ---
    print("\n--- 延时演示 ---")
    print(f"发布延时任务时间: {datetime.datetime.now()}")
    # 使用 publish 方法发布，并携带 task_options
    task_delay.publish(
        msg={"msg": "我是延迟5秒的消息"}, 
        task_options=TaskOptions(countdown=5)
    )

    # --- 9. 定时任务演示 (APScheduler) ---
    print("\n--- 定时演示 (每隔5秒触发一次) ---")
    # 注意：这里是定时“发布”任务到队列，而不是直接运行函数
    ApsJobAdder(task_basic, job_store_kind='memory').add_push_job(
        trigger='interval',
        seconds=5,
        args=(100, 200), # 定时执行 task_basic(100, 200)
        id='my_schedule_job'
    )

    # --- 10. 分组任务发布演示 ---
    print("\n--- 分组任务演示 ---")
    task_group_a_1.push("A1 data")
    task_group_a_2.push("A2 data")
    task_group_b_1.push("B1 data (这条消息不会被消费，因为没启动B组)")

    # --- 11. funboost的asyncio 全链路生态的演示,包括asyncio发布 asyncio消费 asyncio获取结果
    async def rpc_asyncio():
        aio_async_result:AioAsyncResult = await task_async.aio_push("http://site-1.com") # aio_push 返回 AioAsyncResult 对象
        print("RPC 任务已发布，正在asyncio生态等待结果...")
        print(f"aio_async_result RPC 结果: {await aio_async_result.result}") 
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(rpc_asyncio())


    print("\n=== 所有演示任务已发布，ctrl_c_recv使主线程进入监听状态 (按3次 Ctrl+C 退出) ===\n")
    # ctrl_c_recv 阻塞主线程，防止主线程结束了，最好是加上，因为这可以阻止由于主线程结束了导致守护线程结束。 
    # 因为booster.consume() 是在子线程启动的，所以可以连续多个消费函数.consume()而不阻塞主线程
    ctrl_c_recv()