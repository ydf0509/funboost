
# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 14:57
import threading

import time
from funboost import boost, BrokerEnum, BoosterParams


from nb_cache import Cache

# cache = Cache().setup("redis://",prefix='myproj3')
cache = Cache().setup("memory://",prefix='myproj3')


@boost(BoosterParams(queue_name='queue_test2', qps=6, 
                     broker_kind=BrokerEnum.REDIS,
                     consuming_function_decorator = cache.cache(
                        ttl=600,lock=True,key='queue_test2:f2:{a}_{b}',
                        key_include_func = False,
                        ),
                     ))
def f2(a, b):
    sleep_time = 7
    result = a + b
    print(f'消费此消息 {a} + {b} 中。。。。。,此次需要消耗 {sleep_time} 秒')
    time.sleep(sleep_time)  # 模拟做某事需要阻塞n秒种，必须用并发绕过此阻塞。
    print(f'{a} + {b} 的结果是 {result}')
    return result


if __name__ == '__main__':
   
    f2(1000,2000) # 测试直接调用函数
 
    f2.clear()
    for i in range(20):
        f2.push(i, i * 2)
    f2.push(100,200)
    f2.push(100,200)
    f2.consume()

    



