

from funboost.publishers.base_publisher import AbstractPublisher

class MysqlCdcPublisher(AbstractPublisher):
    """
    A placeholder publisher for the CDC broker.
    Publishing is handled automatically by the consumer by listening to binlog events.
    Direct publishing is not supported and will raise an error.
    """

    def _publish_impl(self, msg: str):
        raise NotImplementedError("The 'funboost_cdc' broker does not support manual publishing. "
                                  "Tasks are generated automatically from database changes.")

    def clear(self):
        self.logger.warning("The 'funboost_cdc' broker does not have a queue to clear.")
        pass

    def get_message_count(self):
        return -1 # Not applicable

    def close(self):
        pass