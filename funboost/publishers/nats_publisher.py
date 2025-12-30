from funboost.core.lazy_impoter import NatsImporter
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.funboost_config_deafult import BrokerConnConfig


class NatsPublisher(AbstractPublisher, ):
    """
    使用nats作为中间件
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self.nats_client = NatsImporter().NATSClient(BrokerConnConfig.NATS_URL)
        self.nats_client.connect()

    def _publish_impl(self, msg):
        # print(msg)
        self.nats_client.publish(subject=self.queue_name, payload=msg.encode())

    def clear(self):
        pass

    def get_message_count(self):
        return -1

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass
