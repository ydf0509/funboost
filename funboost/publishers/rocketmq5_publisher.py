# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2026
"""
RocketMQ 5.x 发布者实现，使用最新版 rocketmq-python-client SDK
pip install rocketmq-python-client

支持 RocketMQ 5.x 版本，基于 gRPC 协议
支持 Windows / Linux / macOS
"""

"""
ai写得，等有时间需要测试
"""

import time

from funboost.publishers.base_publisher import AbstractPublisher

# pip install rocketmq-python-client
from rocketmq import ClientConfiguration, Credentials, Producer, Message


class RocketmqPublisher(AbstractPublisher):
    """
    RocketMQ 5.x 发布者，使用 rocketmq-python-client 包
    
    安装方式:
        pip install rocketmq-python-client
        
    特性: 
        - 基于 gRPC 协议，纯 Python 实现
        - 支持 Windows / Linux / macOS
        - 支持 RocketMQ 5.x 版本
        - 支持自动创建 Topic
    """

    _topic__rocketmq_producer = {}
    _created_topics = set()  # 记录已创建的 topic

    def custom_init(self):
        if self._queue_name not in self.__class__._topic__rocketmq_producer:
            # 获取配置
            endpoints = self.publisher_params.broker_exclusive_config['endpoints']
            access_key = self.publisher_params.broker_exclusive_config['access_key']
            secret_key = self.publisher_params.broker_exclusive_config['secret_key']
            namespace = self.publisher_params.broker_exclusive_config['namespace']
            
            # 自动创建 Topic
            self._auto_create_topic(endpoints)
            
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
            
            # 创建 Producer
            producer = Producer(config, [self._queue_name])
            producer.startup()
            
            self.__class__._topic__rocketmq_producer[self._queue_name] = producer
            self.logger.info(f'RocketMQ 5.x Producer 已启动，topic: {self._queue_name}, endpoints: {endpoints}')
        
        self._producer = self.__class__._topic__rocketmq_producer[self._queue_name]

    def _auto_create_topic(self, endpoints: str):
        """
        自动创建 Topic - 通过 HTTP API
        """
        if self._queue_name in self.__class__._created_topics:
            return
        
        host = endpoints.split(':')[0]
        namesrv_addr = self.publisher_params.broker_exclusive_config.get('namesrv_addr') or f'{host}:9876'
        cluster_name = self.publisher_params.broker_exclusive_config.get('cluster_name', 'DefaultCluster')
        
        try:
            self._create_topic_via_http(host, namesrv_addr, cluster_name)
        except Exception as e:
            self.logger.warning(
                f'自动创建 Topic 失败: {e}\n'
                f'请手动创建: docker exec -it rmq-broker sh mqadmin updateTopic -n localhost:9876 -t {self._queue_name} -c {cluster_name}'
            )

    def _create_topic_via_http(self, host: str, namesrv_addr: str, cluster_name: str):
        """通过 HTTP API 创建 Topic"""
        import urllib.request
        import urllib.parse
        import json
        
        # 尝试多个可能的端口和 API
        apis_to_try = [
            # RocketMQ Dashboard API
            (8080, '/topic/createOrUpdate', 'form'),
            # Broker HTTP API  
            (10911, '/topic/createOrUpdate', 'form'),
        ]
        
        for port, path, content_type in apis_to_try:
            try:
                url = f'http://{host}:{port}{path}'
                
                if content_type == 'form':
                    data = urllib.parse.urlencode({
                        'topic': self._queue_name,
                        'clusterName': cluster_name,
                        'readQueueNums': 8,
                        'writeQueueNums': 8,
                    }).encode()
                    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                else:
                    data = json.dumps({
                        'topic': self._queue_name,
                        'clusterName': cluster_name,
                        'readQueueNums': 8,
                        'writeQueueNums': 8,
                    }).encode()
                    headers = {'Content-Type': 'application/json'}
                
                req = urllib.request.Request(url, data=data, method='POST', headers=headers)
                
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        self.logger.info(f'通过 HTTP API ({host}:{port}) 创建 Topic 成功: {self._queue_name}')
                        self.__class__._created_topics.add(self._queue_name)
                        return
            except Exception:
                continue
        
        # 所有方式都失败
        self.logger.warning(
            f'无法自动创建 Topic: {self._queue_name}\n'
            f'请手动执行: docker exec -it <container> sh mqadmin updateTopic -n {namesrv_addr} -t {self._queue_name} -c {cluster_name}'
        )

    def _publish_impl(self, msg: str):
        """发布消息到 RocketMQ Topic"""
        message = Message()
        message.topic = self._queue_name
        message.body = msg.encode('utf-8') if isinstance(msg, str) else msg
        self._producer.send(message)

    def clear(self):
        """清空队列 - RocketMQ 不支持通过 Python SDK 删除消息"""
        self.logger.warning(
            'RocketMQ Python SDK 不支持清空队列/删除消息功能，'
            '如需清空请通过 RocketMQ Console 或 Admin API 操作'
        )

    def get_message_count(self):
        """获取队列消息数量 - RocketMQ Python SDK 不直接支持此功能"""
        if time.time() - getattr(self, '_last_warning_count', 0) > 300:
            setattr(self, '_last_warning_count', time.time())
            self.logger.debug(
                'RocketMQ Python SDK 暂不支持获取队列消息数量，'
                '如需查看请使用 RocketMQ Console'
            )
        return -1

    def close(self):
        """关闭生产者连接"""
        pass
