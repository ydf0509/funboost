"""
这个是用来测试，以redis为中间件，随意关闭代码会不会造成任务丢失的。
"""
import time

from funboost import boost,BrokerEnum

@boost('test_cost_long_time_fun_queue2', broker_kind=BrokerEnum.REDIS_ACK_ABLE, concurrent_num=5)
def cost_long_time_fun(x):
    print(f'正在消费 {x} 中 。。。。')
    time.sleep(3)
    print(f'消费完成 {x} ')

if __name__ == '__main__':
    cost_long_time_fun.consume()