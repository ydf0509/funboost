import json
import os
import threading
import time

from funboost import register_custom_broker, AbstractConsumer, AbstractPublisher,BrokerEnum
from funboost import boost

"""
此文件是演示添加自定义类型的中间件,已python的 list列表作为内存消息队列，这里只是演示怎么自定义扩展中间件，真实不推荐list作为消息队列中间件。

此种方式也可以重写来更改 AbstractConsumer 基类的逻辑,例如你想在任务执行完成后把结果插入到mysql，可以不使用原来推荐的装饰器叠加方式
而是在类中直接重写方法

"""

queue_name__list_map = {}

list_operation_lock = threading.Lock()  # list类型不是线程安全的，queue.Queue是线程安全的，但list不是。


class ListPublisher(AbstractPublisher):
    def __init__(self, *args, **kwargs):
        print('此类可以重写父类 AbstractPublisher 的任何方法，但必须实现以下方法  concrete_realization_of_publish clear  get_message_count  close ')
        super().__init__(*args, **kwargs)
        if self.queue_name not in queue_name__list_map:
            queue_name__list_map[self.queue_name] = []
        self.msg_list: list = queue_name__list_map[self.queue_name]

    def concrete_realization_of_publish(self, msg: str):
        self.msg_list.append(msg)

    def clear(self):
        self.msg_list.clear()

    def get_message_count(self):
        return len(self.msg_list)

    def close(self):
        pass


class ListConsumer(AbstractConsumer):
    def __init__(self, *args, **kwargs):
        print('此类可以重写父类 AbstractConsumer 的任何方法，但必须实现以下方法  _shedual_task  _confirm_consume  _requeue ')
        super().__init__(*args, **kwargs)
        if self.queue_name not in queue_name__list_map:
            queue_name__list_map[self.queue_name] = []
        self.msg_list: list = queue_name__list_map[self.queue_name]

    def _shedual_task(self):
        while True:
            try:
                task_str = self.msg_list.pop(-1)  # pop(0) 消耗的性能更高
            except IndexError:  # 说明是空的
                time.sleep(0.1)
                continue
            kw = {'body': json.loads(task_str)}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass  # 这里不演示基于list作为消息队列中间件的确认消费了

    def _requeue(self, kw):
        self.msg_list.append(json.dumps(kw['body']))


BROKER_KIND_LIST = 101
register_custom_broker(BROKER_KIND_LIST, ListPublisher, ListConsumer)  # 核心，这就是将自己写的类注册到框架中，框架可以自动使用用户的类，这样用户无需修改框架的源代码了。


@boost('test_list_queue', broker_kind=BROKER_KIND_LIST, qps=0.5,concurrent_num=2)
def f(x):
    print(os.getpid())
    print(x * 10)


if __name__ == '__main__':
    for i in range(5000):
        f.push(i)
    print(f.publisher.get_message_count())
    f.multi_process_consume(10)
