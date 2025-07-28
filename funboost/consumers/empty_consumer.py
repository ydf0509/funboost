# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/8 0008 13:32

import abc
from funboost.consumers.base_consumer import AbstractConsumer


class EmptyConsumer(AbstractConsumer, metaclass=abc.ABCMeta):
    """
    一个空的消费者基类，作为自定义 Broker 的模板。

    这个类其实是多余的，因为用户完全可以继承AbstractConsumer，然后实现custom_init方法，然后实现_shedual_task, _confirm_consume, _requeue方法来新增自定义broker。
    这个类是为了清晰明确的告诉你，仅仅需要下面三个方法，就可以实现一个自定义broker，因为AbstractConsumer基类功能太丰富了，基类方法是在太多了，用户不知道需要继承重写哪方法
    
    
    """
    def custom_init(self):
        pass

    @abc.abstractmethod
    def _shedual_task(self):
        """
        核心调度任务。此方法需要实现一个循环，负责从你的中间件中获取消息，
        然后调用 `self._submit_task(msg)` 将任务提交到框架的并发池中执行。 可以参考funboos源码中的各种消费者实现。
        """
        raise NotImplemented('not realization')

    @abc.abstractmethod
    def _confirm_consume(self, kw):
        """确认消费，就是ack概念"""
        raise NotImplemented('not realization')

    @abc.abstractmethod
    def _requeue(self, kw):
        """重新入队"""
        raise NotImplemented('not realization')
