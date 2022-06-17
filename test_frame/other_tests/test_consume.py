# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57
import time
import random
from funboost import boost, LogManager,BrokerEnum




@boost('queue_test2', qps=30, broker_kind=BrokerEnum.REDIS, function_result_status_persistance_conf=)  # 通过设置broker_kind，一键切换中间件为mq或redis等13种中间件或包。
def f2(a, b):
    print(f'消费此消息 {a} + {b} 中。。。。。')
    time.sleep(random.randint(1,1000)/100.0)  # 模拟做某事需要随机消耗一段时间的，精确控频
    print(f'计算 {a} + {b} 得到的结果是  {a + b}')


if __name__ == '__main__':
    f2.clear()
    for i in range(200000):
        f2.push(i, i * 2)
    print(f2.publisher.get_message_count())
    f2.consume()