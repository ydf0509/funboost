# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:32
import json
# import time

from funboost.consumers.base_consumer import AbstractConsumer
from funboost import funboost_config_deafult
import paho.mqtt.client as mqtt


class MqttConsumer(AbstractConsumer):
    """
    emq 作为中间件 实现的消费者 ，使用共享订阅。
    """
    BROKER_KIND = 17

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        # fsdf 表示 funboost.相当于kafka的消费者组作用。
        # 这个是共享订阅，见  https://blog.csdn.net/emqx_broker/article/details/103027813
        self._topic_shared = f'$share/fsdf/{self._queue_name}'

    # noinspection DuplicatedCode
    def _shedual_task(self):
        client = mqtt.Client()
        # client.username_pw_set('admin', password='public')
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.on_disconnect = self._on_socket_close
        client.on_socket_close = self._on_socket_close
        client.connect(funboost_config_deafult.MQTT_HOST, funboost_config_deafult.MQTT_TCP_PORT, 600)  # 600为keepalive的时间间隔
        client.subscribe(self._topic_shared, qos=0)  # on message 是异把消息丢到线程池，本身不可能失败。
        client.loop_forever(retry_first_connection=True)  # 保持连接

    def _on_socket_close(self, client, userdata, socket):
        self.logger.critical(f'{client, userdata, socket}')
        self._shedual_task()

    # noinspection PyPep8Naming
    def _on_disconnect(self, client, userdata, reasonCode, properties):
        self.logger.critical(f'{client, userdata, reasonCode, properties}')

    def _on_connect(self, client, userdata, flags, rc):
        self.logger.info(f'连接mqtt服务端成功, {client, userdata, flags, rc}')

    # noinspection PyUnusedLocal
    def _on_message(self, client, userdata, msg):
        # print(msg.topic + " " + str(msg.payload))
        kw = {'body': json.loads(msg.payload)}
        self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        pass
