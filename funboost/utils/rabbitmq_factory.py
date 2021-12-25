# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 11:51
import pikav0 as pika
import rabbitpy
from pikav0.adapters.blocking_connection import BlockingChannel

from funboost import funboost_config_deafult


class RabbitmqClientRabbitPy:
    """
    使用rabbitpy包。
    """

    # noinspection PyUnusedLocal
    def __init__(self, username, password, host, port, virtual_host, heartbeat=0):
        rabbit_url = f'amqp://{username}:{password}@{host}:{port}/{virtual_host}?heartbeat={heartbeat}'
        self.connection = rabbitpy.Connection(rabbit_url)

    def creat_a_channel(self) -> rabbitpy.AMQP:
        return rabbitpy.AMQP(self.connection.channel())  # 使用适配器，使rabbitpy包的公有方法几乎接近pika包的channel的方法。


class RabbitmqClientPika:
    """
    使用pika包,多线程不安全的包。
    """

    def __init__(self, username, password, host, port, virtual_host, heartbeat=0):
        """
        parameters = pika.URLParameters('amqp://guest:guest@localhost:5672/%2F')

        connection = pika.SelectConnection(parameters=parameters,
                                  on_open_callback=on_open)
        :param username:
        :param password:
        :param host:
        :param port:
        :param virtual_host:
        :param heartbeat:
        """
        credentials = pika.PlainCredentials(username, password)
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            host, port, virtual_host, credentials, heartbeat=heartbeat))
        # self.connection = pika.SelectConnection(pika.ConnectionParameters(
        #     host, port, virtual_host, credentials, heartbeat=heartbeat))

    def creat_a_channel(self) -> BlockingChannel:
        return self.connection.channel()


class RabbitMqFactory:
    def __init__(self, heartbeat=600 , is_use_rabbitpy=0):
        """
        :param heartbeat:
        :param is_use_rabbitpy: 为0使用pika，多线程不安全。为1使用rabbitpy，多线程安全的包。
        """
        if is_use_rabbitpy:
            self.rabbit_client = RabbitmqClientRabbitPy(funboost_config_deafult.RABBITMQ_USER, funboost_config_deafult.RABBITMQ_PASS,
                                                        funboost_config_deafult.RABBITMQ_HOST, funboost_config_deafult.RABBITMQ_PORT,
                                                        funboost_config_deafult.RABBITMQ_VIRTUAL_HOST, heartbeat)
        else:
            self.rabbit_client = RabbitmqClientPika(funboost_config_deafult.RABBITMQ_USER, funboost_config_deafult.RABBITMQ_PASS,
                                                    funboost_config_deafult.RABBITMQ_HOST, funboost_config_deafult.RABBITMQ_PORT,
                                                    funboost_config_deafult.RABBITMQ_VIRTUAL_HOST, heartbeat)

    def get_rabbit_cleint(self):
        return self.rabbit_client
