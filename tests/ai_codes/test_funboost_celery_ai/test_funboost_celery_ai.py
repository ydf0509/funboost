import time
from funboost import boost, BoosterParams, BrokerEnum, ctrl_c_recv
from funboost.assist.celery_helper import CeleryHelper

@boost(BoosterParams(
    queue_name="funboost_celery_queue",
    broker_kind=BrokerEnum.CELERY,
    qps=5,
    max_retry_times=3,
))
def celery_task(user_id: int, message: str):
    """使用celery作为broker的任务函数"""
    print(f"处理用户 {user_id} 的消息: {message}")
    time.sleep(1)  # 模拟处理时间
    return f"用户 {user_id} 的消息处理完成"

@boost(BoosterParams(
    queue_name="funboost_celery_queue2",
    broker_kind=BrokerEnum.CELERY
))
def another_celery_task(data: dict):
    """另一个使用celery作为broker的任务函数"""
    print(f"处理数据: {data}")
    time.sleep(0.5)  # 模拟处理时间
    return f"数据处理完成: {data['key']}"

if __name__ == '__main__':
    print("=== 启动消费者 ===")
    # 启动两个任务的消费者
    celery_task.consume()
    another_celery_task.consume()
    
    print("=== 发布任务 ===")
    # 发布多个任务
    for i in range(10):
        # 使用push方法发布任务
        result = celery_task.push(user_id=i, message=f"Hello Funboost {i}")
        print(f"发布任务 {i}，任务ID: {result.task_id if hasattr(result, 'task_id') else 'N/A'}")
        
        # 发布第二个队列的任务
        another_celery_task.push(data={"key": f"value_{i}", "timestamp": time.time()})
    
    print("=== 启动Celery Worker和Flower ===")
    # 启动Flower监控（可选）
    CeleryHelper.start_flower()
    
    # 启动Celery Worker
    # 注意：在实际生产环境中，你可能需要在单独的进程中启动Celery Worker
    # 这里为了演示，我们在当前进程中启动
    # 重要：Celery worker的并发数是全局设置的，不是每个task单独设置的
    # 可以通过worker_concurrency参数设置并发数，默认为200
    # 例如：CeleryHelper.realy_start_celery_worker(worker_concurrency=10)
    CeleryHelper.realy_start_celery_worker()
    
