# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json

from nameko.containers import ServiceContainer
from nameko.rpc import rpc

from funboost import funboost_config_deafult
from funboost.consumers.base_consumer import AbstractConsumer


class NamekoService3:
    name = 'funboost_nameko_servicedsd'

class NamekoConsumer(AbstractConsumer, ):
    """
    redis作为中间件实现的。
    """
    BROKER_KIND = 2

    def custom_init(self):
        pass
        # url = f'amqp://{funboost_config_deafult.RABBITMQ_USER}:{funboost_config_deafult.RABBITMQ_PASS}@{funboost_config_deafult.RABBITMQ_HOST}:{funboost_config_deafult.RABBITMQ_PORT}/{funboost_config_deafult.RABBITMQ_VIRTUAL_HOST}'
        #
        # self._nameko_config = {'AMQP_URI': url}
        #
        # class MyService(NamekoService):
        #
        #     @rpc
        #     def call(this, *args, **kwargs):
        #         self.consuming_function(*args, **kwargs)
        #
        # self._nameko_service_cls  = MyService


    def _shedual_task(self):
        url = f'amqp://{funboost_config_deafult.RABBITMQ_USER}:{funboost_config_deafult.RABBITMQ_PASS}@{funboost_config_deafult.RABBITMQ_HOST}:{funboost_config_deafult.RABBITMQ_PORT}/{funboost_config_deafult.RABBITMQ_VIRTUAL_HOST}'

        self._nameko_config = {'AMQP_URI': url}

        class MyService():
            name = 'funboost_nameko_service'
            @rpc
            def call(this, *args, **kwargs):
                self.consuming_function(*args, **kwargs)

        self._nameko_service_cls = MyService

        container = ServiceContainer(self._nameko_service_cls, config=self._nameko_config)

        container.start()
        container.wait()

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        pass


