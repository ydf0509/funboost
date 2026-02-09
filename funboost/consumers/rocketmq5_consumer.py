# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2026
"""
RocketMQ 5.x 消费者实现，使用最新版 rocketmq-python-client SDK
pip install rocketmq-python-client

使用 SimpleConsumer 模式：
- 支持单条消息乱序 ACK，不依赖 offset
- 基于 gRPC 协议，纯 Python 实现
- 支持 Windows / Linux / macOS
"""


"""
ai写得，等有时间需要测试
"""

import time

from funboost.consumers.base_consumer import AbstractConsumer

# pip install rocketmq-python-client
try:
    from rocketmq import ClientConfiguration, Credentials, FilterExpression, SimpleConsumer
except ImportError:
    raise ImportError(
        '需要安装 rocketmq-python-client 包: pip install rocketmq-python-client\n'
        '这是 RocketMQ 5.x 的官方 Python SDK，支持 Windows/Linux/macOS'
    )
class RocketmqConsumer(AbstractConsumer):
    """
    RocketMQ 5.x 消费者，使用 SimpleConsumer 模式
    
    安装方式:
        pip install rocketmq-python-client
        
    特性: 
        - SimpleConsumer 模式：支持单条消息乱序 ACK，不依赖 offset
        - 基于 gRPC 协议，纯 Python 实现
        - 支持 Windows / Linux / macOS
        - 支持 RocketMQ 5.x 版本
        - 消息重入队使用原生 invisible_duration 机制，不 ACK 的消息超时后自动重新可见
        
    broker_exclusive_config 可配置参数:
        - endpoints: RocketMQ gRPC 端点地址，默认 '127.0.0.1:8081'
        - consumer_group: 消费者组名，默认 'funboost_consumer_group'
        - access_key: 访问密钥（可选）
        - secret_key: 密钥（可选）
        - namespace: 命名空间（可选）
        - invisible_duration: 消息不可见时间（秒），消息取出后在此时间内对其他消费者不可见，默认 15
        - max_message_num: 每次拉取的最大消息数，默认 32
        - tag: 消息过滤 tag，默认 '*' 表示不过滤
    """

    def custom_init(self):
        self._consumer = None

    def _dispatch_task(self):
        """从 RocketMQ 拉取消息并分发到并发池执行"""
        

        # 获取配置参数
        endpoints = self.consumer_params.broker_exclusive_config['endpoints']
        consumer_group = self.consumer_params.broker_exclusive_config['consumer_group']
        access_key = self.consumer_params.broker_exclusive_config['access_key']
        secret_key = self.consumer_params.broker_exclusive_config['secret_key']
        namespace = self.consumer_params.broker_exclusive_config['namespace']
        invisible_duration = self.consumer_params.broker_exclusive_config['invisible_duration']
        max_message_num = self.consumer_params.broker_exclusive_config['max_message_num']
        tag = self.consumer_params.broker_exclusive_config['tag']

        # 创建凭证
        if access_key and secret_key:
            credentials = Credentials(access_key, secret_key)
        else:
            credentials = Credentials()

        # 创建客户端配置
        if namespace:
            config = ClientConfiguration(endpoints, credentials, namespace)
        else:
            config = ClientConfiguration(endpoints, credentials)

        # 创建订阅表达式
        if tag and tag != '*':
            filter_expression = FilterExpression(tag)
        else:
            filter_expression = FilterExpression()

        # 创建 SimpleConsumer
        self._consumer = SimpleConsumer(
            config,
            consumer_group,
            {self._queue_name: filter_expression}
        )

        self.logger.info(
            f'RocketMQ 5.x SimpleConsumer 正在启动，consumer_group: {consumer_group}, '
            f'topic: {self._queue_name}, endpoints: {endpoints}, invisible_duration: {invisible_duration}s'
        )

        # 启动消费者
        self._consumer.startup()
        self.logger.info(f'RocketMQ 5.x SimpleConsumer 已启动并订阅 topic: {self._queue_name}')

        # SimpleConsumer 拉模式循环消费
        while True:
            try:
                # 拉取消息
                # receive(max_message_num, invisible_duration_seconds)
                messages = self._consumer.receive(max_message_num, invisible_duration)
                
                if messages is None:
                    continue
                    
                for msg in messages:
                    # 构建 kw 字典，包含消息和用于 ACK 的信息
                    try:
                        body = msg.body.decode('utf-8') if isinstance(msg.body, bytes) else msg.body
                    except (UnicodeDecodeError, AttributeError):
                        body = msg.body
                        
                    kw = {
                        'body': body,
                        'rocketmq_msg': msg,  # 保存原始消息对象用于 ACK
                        'message_id': msg.message_id,
                    }
                    self._submit_task(kw)
                    
            except Exception as e:
                self.logger.error(f'RocketMQ SimpleConsumer 拉取消息出错: {e}', exc_info=True)
                time.sleep(1)

    def _confirm_consume(self, kw):
        """
        确认消费 - SimpleConsumer 支持单条消息乱序 ACK
        每条消息可以独立确认，不依赖 offset
        """
        msg = kw.get('rocketmq_msg')
        if msg and self._consumer:
            try:
                self._consumer.ack(msg)
            except Exception as e:
                self.logger.error(f'RocketMQ ACK 消息失败: {e}', exc_info=True)

    def _requeue(self, kw):
        """
        消息重入队列 - 使用 RocketMQ 原生的 invisible_duration 机制
        
        通过 change_invisible_duration 将消息的不可见时间设置为 0，
        使消息立即重新可见，可以被重新消费。
        
        如果 SDK 不支持 change_invisible_duration，则不做任何操作，
        消息会在 invisible_duration 超时后自动重新可见。
        """
        msg = kw.get('rocketmq_msg')
        if msg and self._consumer:
            try:
                # 尝试使用 change_invisible_duration 立即让消息重新可见
                self._consumer.change_invisible_duration(msg, 0)
                self.logger.debug(f'RocketMQ 消息 {msg.message_id} 已设置为立即重新可见')
            except AttributeError:
                # SDK 不支持 change_invisible_duration，消息会在 invisible_duration 超时后自动重新可见
                self.logger.debug(
                    f'RocketMQ 消息 {msg.message_id} 将在 invisible_duration 超时后自动重新可见'
                )
            except Exception as e:
                self.logger.warning(f'RocketMQ change_invisible_duration 失败: {e}，消息将在超时后自动重新可见')
