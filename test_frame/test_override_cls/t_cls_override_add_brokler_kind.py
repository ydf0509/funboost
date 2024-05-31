import json

import time
from collections import defaultdict
from funboost import boost, BrokerEnum, BoosterParams, AbstractConsumer, FunctionResultStatus, EmptyConsumer, EmptyPublisher

queue_name__list_map = defaultdict(list)


class MyListConsumer(EmptyConsumer):
    def custom_init(self):
        self.list: list = queue_name__list_map[self.queue_name]

    def _shedual_task(self):
        while True:
            try:
                msg = self.list.pop()
                self._submit_task({'body': msg})
            except IndexError:
                time.sleep(1)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        self.list.append(kw['body'])


class MyListPublisher(EmptyPublisher):
    def custom_init(self):
        self.list: list = queue_name__list_map[self.queue_name]

    def concrete_realization_of_publish(self, msg: str):
        self.list.append(json.loads(msg))

    def clear(self):
        self.list.clear()

    def get_message_count(self):
        return len(self.list)

    def close(self):
        pass


@boost(BoosterParams(queue_name='test_define_cls_queue', broker_kind=BrokerEnum.EMPTY,
                     concurrent_num=10, consumer_override_cls=MyListConsumer,publisher_override_cls=MyListPublisher,
                     is_show_message_get_from_broker=True))
def cost_long_time_fun(x):
    print(f'start {x}')
    time.sleep(20)
    print(f'end {x}')


if __name__ == '__main__':
    for i in range(100):
        cost_long_time_fun.push(i)
    cost_long_time_fun.consume()
