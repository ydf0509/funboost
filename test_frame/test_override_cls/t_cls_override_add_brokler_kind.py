import threading
import json
import time
from collections import defaultdict
from funboost import boost, BrokerEnum, BoosterParams, EmptyConsumer, EmptyPublisher

queue_name__list_map = defaultdict(list)
list_lock = threading.Lock()

'''
使用 list 列表作为 消息队列的中间件 实现, 通过指定 consumer_override_cls 和 publisher_override_cls 为用户自定义的类来实现新增消息队列种类。
'''


class MyListConsumer(EmptyConsumer):
    def custom_init(self):
        self.list: list = queue_name__list_map[self.queue_name]

    def _shedual_task(self):
        while True:
            try:
                with list_lock:
                    msg = self.list.pop()
                self._submit_task({'body': msg})
            except IndexError:
                time.sleep(1)

    def _confirm_consume(self, kw):
        """ 这里是演示,所以搞简单一点,不实现确认消费 """
        pass

    def _requeue(self, kw):
        with list_lock:
            self.list.append(kw['body'])


class MyListPublisher(EmptyPublisher):
    def custom_init(self):
        self.list: list = queue_name__list_map[self.queue_name]

    def concrete_realization_of_publish(self, msg: str):
        with list_lock:
            self.list.append(msg)

    def clear(self):
        with list_lock:
            self.list.clear()

    def get_message_count(self):
        with list_lock:
            return len(self.list)

    def close(self):
        pass


'''
完全重新自定义增加中间件时候,broker_kind 建议指定为 BrokerEnum.EMPTY
'''


@boost(BoosterParams(queue_name='test_define_list_queue',
                     broker_kind=BrokerEnum.EMPTY,  # 完全重新自定义新增中间件时候,broker_kind 请指定 BrokerEnum.EMPTY
                     concurrent_num=1, consumer_override_cls=MyListConsumer, publisher_override_cls=MyListPublisher,
                     is_show_message_get_from_broker=True))
def cost_long_time_fun(x):
    print(f'start {x}')
    time.sleep(20)
    print(f'end {x}')


if __name__ == '__main__':

    for i in range(100):
        cost_long_time_fun.push(i)
    cost_long_time_fun.consume()
