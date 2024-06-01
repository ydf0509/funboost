# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/8 0008 12:12

import abc
from funboost.publishers.base_publisher import AbstractPublisher


class EmptyPublisher(AbstractPublisher, metaclass=abc.ABCMeta):
    """
    空的发布者，空的实现，需要搭配 boost入参的 consumer_override_cls 和 publisher_override_cls使用，或者被继承。
    """

    def custom_init(self):
        pass

    @abc.abstractmethod
    def concrete_realization_of_publish(self, msg: str):
        raise NotImplemented('not realization')

    @abc.abstractmethod
    def clear(self):
        raise NotImplemented('not realization')

    @abc.abstractmethod
    def get_message_count(self):
        raise NotImplemented('not realization')

    @abc.abstractmethod
    def close(self):
        raise NotImplemented('not realization')
