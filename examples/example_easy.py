"""
Funboost 最最基础示例
演示如何使用 @boost 装饰器创建分布式任务队列
"""
import time
from funboost import boost, BrokerEnum, BoosterParams,ctrl_c_recv


# 示例1: 最简单的任务函数
@boost(BoosterParams(
    queue_name="demo_queue_1",
    broker_kind=BrokerEnum.SQLITE_QUEUE,  # 使用 SQLite 作为消息队列，无需额外安装中间件
    qps=5,  # 每秒执行5次
    concurrent_num=10,  # 并发数为10
))
def add_task(x, y):
    """简单的加法任务"""
    print(f'计算: {x} + {y} = {x + y}')
    time.sleep(1)  # 模拟耗时操作
    return x + y


if __name__ == '__main__':
    for i in range(10):
        add_task.push(i, i * 2)
        add_task.publish({"x":i*10, "y": i * 20})

        # 可以通过 generate_msg_context_for_push 和 generate_msg_context_for_publish 预览发布消息，即使你不发布，也可以查看最终要发送的消息是什么样。
        print(add_task.publisher.generate_msg_context_for_push(i, i * 2).msg_json) 
        print(add_task.publisher.generate_msg_context_for_publish({"x":i*10, "y": i * 20},task_id=f'task_{10000+i}'))
        
        
    add_task.consume()
    ctrl_c_recv()