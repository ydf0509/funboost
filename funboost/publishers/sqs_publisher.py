# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2026/1/12
"""
使用 AWS SQS 作为消息队列中间件的发布者实现。
使用 boto3 SDK 操作 SQS。

AWS SQS 是亚马逊的托管消息队列服务，支持：
- 标准队列（高吞吐量，至少一次传递）
- FIFO 队列（严格顺序，恰好一次处理）
- 消息可见性超时
- 消息确认删除机制

使用前需要安装 boto3: pip install boto3
"""
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.funboost_config_deafult import BrokerConnConfig


class SqsPublisher(AbstractPublisher):
    """
    使用 AWS SQS 作为消息队列中间件的发布者。
    
    原生实现比通过 kombu 间接使用 SQS 性能更强。
    支持标准队列和 FIFO 队列。
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        """初始化 SQS 客户端和队列"""
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
        
        # 获取或创建队列
        self._queue_url = self._get_or_create_queue()
        self.logger.info(f'SQS 队列已就绪: {self._queue_url}')

    def _get_or_create_queue(self) -> str:
        """获取队列URL，如果队列不存在则创建"""
        try:
            # 尝试获取已存在的队列
            response = self._sqs_client.get_queue_url(QueueName=self._queue_name)
            return response['QueueUrl']
        except self._sqs_client.exceptions.QueueDoesNotExist:
            # 创建新队列
            self.logger.info(f'SQS 队列 {self._queue_name} 不存在，正在创建...')
            
            # 从 broker_exclusive_config 获取队列属性
            broker_config = self.publisher_params.broker_exclusive_config
            visibility_timeout = broker_config['visibility_timeout']
            message_retention_period = broker_config['message_retention_period']
            
            attributes = {
                'VisibilityTimeout': str(visibility_timeout),
                'MessageRetentionPeriod': str(message_retention_period),
            }
            
            # 如果队列名以 .fifo 结尾，则创建 FIFO 队列
            if self._queue_name.endswith('.fifo'):
                attributes['FifoQueue'] = 'true'
                content_based_deduplication = broker_config['content_based_deduplication']
                attributes['ContentBasedDeduplication'] = 'true' if content_based_deduplication else 'false'
            
            response = self._sqs_client.create_queue(
                QueueName=self._queue_name,
                Attributes=attributes
            )
            return response['QueueUrl']

    def _publish_impl(self, msg: str):
        """发布消息到 SQS 队列"""
        send_kwargs = {
            'QueueUrl': self._queue_url,
            'MessageBody': msg,
        }
        
        # FIFO 队列需要 MessageGroupId
        if self._queue_name.endswith('.fifo'):
            # 使用队列名作为默认的消息组ID，保证同一队列的消息顺序
            send_kwargs['MessageGroupId'] = self._queue_name
        
        self._sqs_client.send_message(**send_kwargs)

    def clear(self):
        """清空队列中的所有消息"""
        try:
            self._sqs_client.purge_queue(QueueUrl=self._queue_url)
            self.logger.warning(f'已清空 SQS 队列 {self._queue_name} 中的所有消息')
        except Exception as e:
            # PurgeQueue 有60秒的冷却期，如果刚清空过可能会失败
            self.logger.error(f'清空队列失败: {e}')

    def get_message_count(self) -> int:
        """获取队列中的消息数量（近似值）"""
        response = self._sqs_client.get_queue_attributes(
            QueueUrl=self._queue_url,
            AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
        )
        attrs = response['Attributes']
        # 返回可见消息数 + 正在处理的消息数
        visible = int(attrs['ApproximateNumberOfMessages'])
        not_visible = int(attrs['ApproximateNumberOfMessagesNotVisible'])
        return visible + not_visible

    def close(self):
        """清理资源"""
        # boto3 客户端不需要显式关闭
        pass
