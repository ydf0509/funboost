# -*- coding: utf-8 -*-
"""
测试 librabbitmq broker 的基本功能

注意：
1. 需要先安装 librabbitmq: pip install librabbitmq
2. librabbitmq 主要支持 Linux 环境，Windows 上编译安装可能有问题
3. 需要确保 RabbitMQ 服务正在运行
"""
from auto_run_on_remote import run_current_script_on_remote
run_current_script_on_remote() 
from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(
    queue_name='test_librabbitmq_queue',
    broker_kind=BrokerEnum.RABBITMQ_LIBRABBITMQ,
    concurrent_num=10,
    qps=5,
))
def test_librabbitmq_task(x, y):
    """测试任务函数"""
    print(f'{x} + {y} = {x + y}')
    return x + y


if __name__ == '__main__':
    # 发布5个测试任务
    for i in range(5):
        test_librabbitmq_task.push(i, i * 2)
    
    print("已发布5个任务到 test_librabbitmq_queue 队列")
    
    # 启动消费
    test_librabbitmq_task.consume()
