# -*- coding: utf-8 -*-
"""
测试 RABBITMQ_AMQP broker 的基本功能

amqp 是 Celery/Kombu 底层使用的高效 AMQP 客户端，
无需额外安装（已随 celery/kombu 安装）
"""
from auto_run_on_remote import run_current_script_on_remote
run_current_script_on_remote() 

import time
from funboost import boost, BoosterParams, BrokerEnum,ctrl_c_recv


@boost(BoosterParams(
    queue_name='test_rabbitmq_amqp_queue',
    broker_kind=BrokerEnum.RABBITMQ_AMQP,
    concurrent_num=200,
    # qps=5,
    log_level=20,
    broker_exclusive_config= {'no_ack':True}
))
def test_rabbitmq_amqp_task(x, y):
    """测试任务函数"""
    # print(f'{x} + {y} = {x + y}')
    if x % 10000 == 0:
        print(f'{x} + {y} = {x + y}')
    return x + y


if __name__ == '__main__':
    # print('hello')
    
    # 发布5个测试任务
    for i in range(50000):
        if i % 10000 == 0:
            print(f'发布 {i} 个任务到 test_rabbitmq_amqp_queue 队列')
        test_rabbitmq_amqp_task.push(i, i * 2)
    
    # print("已发布5个任务到 test_rabbitmq_amqp_queue 队列")
    
     # 启动消费
    test_rabbitmq_amqp_task.consume()
    
    
    # ctrl_c_recv()
    
    
    # time.sleep(1000)
    
    # test_rabbitmq_amqp_task.push(10, 20)
