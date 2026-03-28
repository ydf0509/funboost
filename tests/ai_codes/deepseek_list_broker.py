

# -*- coding: utf-8 -*-
"""
演示如何将 Python 内置的 list 作为 Funboost 的消息队列（Broker）。
本文件独立运行，无需额外安装 Redis、RabbitMQ 等中间件。
"""

import time
import threading
from collections import defaultdict
from funboost import boost, BrokerEnum, BoosterParams, ctrl_c_recv, EmptyConsumer, EmptyPublisher
from funboost.constant import BrokerEnum as OriginalBrokerEnum


# ---------- 1. 定义全局数据结构 ----------
# 使用字典存储不同队列名对应的列表
queue_list_map = defaultdict(list)
# 添加锁以保证线程安全（列表操作本身是原子的，但多线程同时修改可能导致问题）
list_lock = threading.Lock()


# ---------- 2. 自定义消费者 ----------
class ListConsumer(EmptyConsumer):
    """
    从 list 中消费消息的消费者。
    注意：此实现不包含真正的 ACK 机制，仅做演示。
    实际使用中可重写 _confirm_consume 和 _requeue 方法实现可靠消费。
    """

    def custom_init(self):
        """初始化：获取当前队列对应的列表"""
        self.queue_list = queue_list_map[self.queue_name]

    def _dispatch_task(self):
        """核心调度循环：不断从列表中取消息并提交给框架"""
        while True:
            try:
                with list_lock:
                    if self.queue_list:
                        msg = self.queue_list.pop(0)  # 先进先出
                    else:
                        msg = None
                if msg is not None:
                    # 将消息包装成框架需要的格式，然后提交
                    self._submit_task({'body': msg})
                else:
                    # 无消息时短暂休眠，避免空转
                    time.sleep(0.01)
            except Exception as e:
                self.logger.error(f"调度出错: {e}")

    def _confirm_consume(self, kw):
        """确认消费（简单实现：什么都不做）"""
        # 实际生产环境中可在此处删除或归档消息
        pass

    def _requeue(self, kw):
        """重新入队（简单实现：将消息放回列表头部）"""
        with list_lock:
            self.queue_list.insert(0, kw['body'])


# ---------- 3. 自定义生产者 ----------
class ListPublisher(EmptyPublisher):
    """
    向 list 中发布消息的生产者。
    """

    def custom_init(self):
        """初始化：获取当前队列对应的列表"""
        self.queue_list = queue_list_map[self.queue_name]

    def _publish_impl(self, msg: str):
        """实际发布逻辑：将消息添加到列表尾部"""
        with list_lock:
            self.queue_list.append(msg)

    def clear(self):
        """清空队列"""
        with list_lock:
            self.queue_list.clear()

    def get_message_count(self):
        """获取当前队列中的消息数量"""
        with list_lock:
            return len(self.queue_list)

    def close(self):
        """关闭连接（本例无资源需要关闭）"""
        pass


# ---------- 4. 注册自定义 Broker ----------
# 使用一个自定义的 Broker 名称，避免与内置 Broker 冲突
MY_LIST_BROKER = 'MY_LIST_BROKER'

# 注册到 Funboost
from funboost.factories.broker_kind__publsiher_consumer_type_map import register_custom_broker
register_custom_broker(MY_LIST_BROKER, ListPublisher, ListConsumer)


# ---------- 5. 定义任务函数 ----------
@boost(BoosterParams(
    queue_name='demo_list_queue',
    broker_kind=MY_LIST_BROKER,   # 使用我们自定义的 list broker
    qps=5,                         # 每秒最多执行5次
    concurrent_num=3,              # 并发数3
    is_show_message_get_from_broker=True,   # 打印取出的消息内容
))
def add(a: int, b: int) -> int:
    """简单的加法任务"""
    result = a + b
    print(f"计算: {a} + {b} = {result}")
    time.sleep(0.5)  # 模拟耗时操作
    return result


# ---------- 6. 测试代码 ----------
if __name__ == '__main__':
    # 清空队列（可选）
    add.clear()
    print(f"队列初始消息数: {add.get_message_count()}")

    # 发布 20 条消息
    for i in range(20):
        add.push(i, i * 2)
        # 也可以使用 publish 发布字典
        # add.publish({'a': i, 'b': i * 2})

    print(f"发布后消息数: {add.get_message_count()}")

    # 启动消费者（非阻塞，在后台线程运行）
    add.consume()

    # 等待一段时间，让消费者处理一些任务
    time.sleep(5)

    # 查看剩余消息数
    print(f"5秒后剩余消息数: {add.get_message_count()}")

    # 继续等待直到所有消息处理完毕
    # 注意：由于我们使用的是内存 list，消息处理完后队列为空
    # 但消费者线程会继续运行（空闲等待），主线程不能退出
    # 因此使用 ctrl_c_recv() 阻塞主线程，方便用 Ctrl+C 退出
    print("按 Ctrl+C 停止程序...")
    ctrl_c_recv()