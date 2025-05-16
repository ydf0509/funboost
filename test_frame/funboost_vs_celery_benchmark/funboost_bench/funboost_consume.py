from funboost import boost, BrokerEnum,BoosterParams,ConcurrentModeEnum
import datetime
import logging

@boost(BoosterParams(queue_name='test_queue_funboost01', 
                     broker_kind=BrokerEnum.REDIS,log_level=logging.INFO,
                     concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
                     )
                     )
def print_number(i):
    if  i % 1000 == 0:
        print(f"{datetime.datetime.now()} 当前数字是: {i}")
    return i  # 返回结果方便查看任务执行状态


if __name__ == '__main__':
    print_number.consume()


'''

在win11 + python3.9 + funboost + redis 中间件 + amd r7 5800h cpu 环境下测试 + 选择单线程并发模式

funboost消费性能测试结果如下：

funboost平均每隔0.15秒消费1000条消息，10万消息在15秒内全部完成了，每秒能消费7000条消息

'''