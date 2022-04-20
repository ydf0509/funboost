import json
import threading
import time
from collections import deque
from funboost import register_custom_broker, AbstractConsumer, AbstractPublisher
from funboost import boost

"""
此文件是演示添加自定义类型的中间件,已python的 deque 作为内存消息队列，这里只是演示怎么自定义扩展中间件

此种方式也可以在子类中重写来更改 AbstractConsumer 基类的逻辑,例如你想在任务执行完成后把结果插入到mysql或者做更精细化的定制流程，可以不使用原来推荐的装饰器叠加方式
而是在类中直接重写方法

"""

queue_name__deque_map = {}


class DequePublisher(AbstractPublisher):
    def __init__(self, *args, **kwargs):
        print('此类可以重写父类 AbstractPublisher 的任何方法，但必须实现以下方法  concrete_realization_of_publish clear  get_message_count  close ')
        super().__init__(*args, **kwargs)
        if self.queue_name not in queue_name__deque_map:
            queue_name__deque_map[self.queue_name] = deque()
        self.msg_deque: deque = queue_name__deque_map[self.queue_name]

    def concrete_realization_of_publish(self, msg: str):
        self.msg_deque.append(msg)

    def clear(self):
        self.msg_deque.clear()

    def get_message_count(self):
        return len(self.msg_deque)

    def close(self):
        pass


class DequeConsumer(AbstractConsumer):
    def __init__(self, *args, **kwargs):
        print('此类可以重写父类 AbstractConsumer 的任何方法，但必须实现以下方法  _shedual_task  _confirm_consume  _requeue ')
        super().__init__(*args, **kwargs)
        if self.queue_name not in queue_name__deque_map:
            queue_name__deque_map[self.queue_name] = deque()
        self.msg_deque: deque = queue_name__deque_map[self.queue_name]

    def _shedual_task(self):
        while True:
            try:
                task_str = self.msg_deque.popleft()
            except IndexError:  # 说明是空的
                time.sleep(0.1)
                continue
            kw = {'body': json.loads(task_str)}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass  # 这里不演示基于list作为消息队列中间件的确认消费了

    def _requeue(self, kw):
        self.msg_deque.append(json.dumps(kw['body']))


BROKER_KIND_DEQUE = 102
register_custom_broker(BROKER_KIND_DEQUE, DequePublisher, DequeConsumer)  # 核心，这就是将自己写的类注册到框架中，框架可以自动使用用户的类，这样用户无需修改框架的源代码了。


@boost('test_list_queue', broker_kind=BROKER_KIND_DEQUE, qps=10, )
def f(x):
    print(x * 10)


if __name__ == '__main__':
    for i in range(50):
        f.push(i)
    print(f.publisher.get_message_count())
    f.consume()
