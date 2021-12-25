# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 12:12
from funboost.publishers.base_publisher import AbstractPublisher
from funboost import funboost_config_deafult

"""
首先安装mqtt模块：


pip install paho-mqtt
写一个发布客户端pub.py：

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code: " + str(rc))

def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect('127.0.0.1', 1883, 600) # 600为keepalive的时间间隔
client.publish('fifa', payload='amazing', qos=0)






再写一个接受客户端sub.py：

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code: " + str(rc))

def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect('127.0.0.1', 1883, 600) # 600为keepalive的时间间隔
client.subscribe('fifa', qos=0)
client.loop_forever() # 保持连接

作者：赤色要塞满了
链接：https://www.jianshu.com/p/0ed4e59b1e8f
来源：简书
著作权归作者所有。商业转载请联系作者获得授权，非商业转载请注明出处。
"""

import paho.mqtt.client as mqtt


# def on_connect(client, userdata, flags, rc):
#     print("Connected with result code: " + str(rc))
#
#
# def on_message(client, userdata, msg):
#     print(msg.topic + " " + str(msg.payload))


class MqttPublisher(AbstractPublisher, ):
    """
    使用 emq 作为中间件
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        client = mqtt.Client()
        # client.username_pw_set('admin', password='public')
        client.on_connect = self._on_connect
        client.on_socket_close = self._on_socket_close
        # client.on_message = on_message
        # print(frame_config.MQTT_HOST)
        client.connect(funboost_config_deafult.MQTT_HOST, funboost_config_deafult.MQTT_TCP_PORT, 600)  # 600为keepalive的时间间隔
        self._client = client

    def _on_socket_close(self, client, userdata, socket):
        self.logger.critical(f'{client, userdata, socket}')
        self.custom_init()

    def _on_connect(self, client, userdata, flags, rc):
        self.logger.info(f'连接mqtt服务端成功, {client, userdata, flags, rc}')

    def concrete_realization_of_publish(self, msg):
        self._client.publish(self._queue_name, payload=msg, qos=0, retain=False)

    def clear(self):
        pass
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    def get_message_count(self):
        # nb_print(self.redis_db7,self._queue_name)
        return -1

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass
