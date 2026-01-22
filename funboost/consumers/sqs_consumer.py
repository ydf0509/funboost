# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2026/1/12
"""
使用 AWS SQS 作为消息队列中间件的消费者实现。
使用 boto3 SDK 操作 SQS。

支持：
- 长轮询（Long Polling）减少空轮询
- 批量拉取消息提高效率
- 消息确认（通过删除消息实现）
- 消息重入队

使用前需要安装 boto3: pip install boto3
"""
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.sqs_publisher import SqsPublisher
from funboost.core.func_params_model import PublisherParams


class SqsConsumer(AbstractConsumer):
    """
    使用 AWS SQS 作为消息队列中间件的消费者。
    
    支持消息确认删除机制，确保消息不丢失。
    在消费失败时支持消息重入队。
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        """初始化 SQS 客户端"""
        import boto3
        
        # 构建 boto3 客户端参数
        client_kwargs = {
            'region_name': BrokerConnConfig.SQS_REGION_NAME,
        }
        
        # 如果配置了显式凭证，则使用
        if BrokerConnConfig.SQS_AWS_ACCESS_KEY_ID and BrokerConnConfig.SQS_AWS_SECRET_ACCESS_KEY:
            client_kwargs['aws_access_key_id'] = BrokerConnConfig.SQS_AWS_ACCESS_KEY_ID
            client_kwargs['aws_secret_access_key'] = BrokerConnConfig.SQS_AWS_SECRET_ACCESS_KEY
        
        # 如果配置了自定义端点（用于 LocalStack 等），则使用
        if BrokerConnConfig.SQS_ENDPOINT_URL:
            client_kwargs['endpoint_url'] = BrokerConnConfig.SQS_ENDPOINT_URL
        
        self._sqs_client = boto3.client('sqs', **client_kwargs)
        
        # 获取队列URL（使用发布者的方法来确保队列存在）
        self._sqs_publisher = SqsPublisher(publisher_params=PublisherParams(queue_name=self.queue_name))
        self._queue_url = self._sqs_publisher._queue_url
        
        # 从 broker_exclusive_config 获取配置
        self._wait_time_seconds = self.consumer_params.broker_exclusive_config['wait_time_seconds']  # 长轮询等待时间
        self._max_number_of_messages = self.consumer_params.broker_exclusive_config['max_number_of_messages']  # 每次拉取的最大消息数
        self._visibility_timeout = self.consumer_params.broker_exclusive_config['visibility_timeout']  # 可见性超时（秒）

    def _dispatch_task(self):
        """从 SQS 队列拉取消息并提交任务"""
        while True:
 
            # 使用长轮询接收消息
            response = self._sqs_client.receive_message(
                QueueUrl=self._queue_url,
                MaxNumberOfMessages=self._max_number_of_messages,
                WaitTimeSeconds=self._wait_time_seconds,
                VisibilityTimeout=self._visibility_timeout,
                AttributeNames=['All'],
                MessageAttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            
            if messages:
                self._print_message_get_from_broker([msg['Body'] for msg in messages])
                
                for message in messages:
                    # 构建任务关键字参数
                    kw = {
                        'body': message['Body'],
                        'receipt_handle': message['ReceiptHandle'],  # 用于确认消费
                        'message_id': message['MessageId'],
                    }
                    self._submit_task(kw)
            # 无消息时长轮询已等待 WaitTimeSeconds，无需额外 sleep


    def _confirm_consume(self, kw):
        """
        确认消费消息。
        
        在 SQS 中，确认消费是通过删除消息实现的。
        如果不删除，消息会在 VisibilityTimeout 后重新可见。
        """
        receipt_handle = kw['receipt_handle']
        try:
            self._sqs_client.delete_message(
                QueueUrl=self._queue_url,
                ReceiptHandle=receipt_handle
            )
        except Exception as e:
            self.logger.error(f'确认消费（删除消息）失败: {e}')

    def _requeue(self, kw):
        """
        重新入队。
        
        由于 SQS 的消息在 VisibilityTimeout 后会自动重新可见，
        这里我们可以：
        1. 立即改变消息可见性为0，让它马上重新可见
        2. 或者重新发送消息到队列
        
        这里采用方案2，因为更可靠，且可以保留原始消息体。
        """
        body = kw['body']
        # 重新发送消息
        self._sqs_publisher.publish(body)
        
        # 删除原消息（避免重复）
        receipt_handle = kw['receipt_handle']
        try:
            self._sqs_client.delete_message(
                QueueUrl=self._queue_url,
                ReceiptHandle=receipt_handle
            )
        except Exception as e:
            self.logger.error(f'确认消费（删除消息）失败: {e}, body:{body}')
            pass  # 忽略删除失败，因为消息可能已经超时

