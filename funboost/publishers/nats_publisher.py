from pynats import NATSClient  # noqa
from funboost.publishers.base_publisher import AbstractPublisher
from funboost import funboost_config_deafult


class NatsPublisher(AbstractPublisher, ):
    """
    使用nats作为中间件
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self.nats_client = NATSClient(funboost_config_deafult.NATS_URL)
        self.nats_client.connect()

    def concrete_realization_of_publish(self, msg):
        # print(msg)
        self.nats_client.publish(subject=self.queue_name, payload=msg.encode())

    def clear(self):
        pass

    def get_message_count(self):
        return -1

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass
