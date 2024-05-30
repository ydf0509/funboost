# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/8 0008 13:32

import abc
from funboost.consumers.base_consumer import AbstractConsumer


class EmptyConsumer(AbstractConsumer, metaclass=abc.ABCMeta):
    """
    空的消费者没实现，空的实现，需要搭配 boost入参的 consumer_override_cls 和 publisher_override_cls使用，或者被继承。
    """

    @abc.abstractmethod
    def _shedual_task(self):
        raise NotImplemented('not realization')

    @abc.abstractmethod
    def _confirm_consume(self, kw):
        raise NotImplemented('not realization')

    @abc.abstractmethod
    def _requeue(self, kw):
        raise NotImplemented('not realization')
