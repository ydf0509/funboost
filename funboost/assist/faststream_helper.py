import asyncio

from faststream import FastStream
from faststream.rabbit import RabbitBroker
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.core.loggers import get_funboost_file_logger

get_funboost_file_logger('faststream.access.rabbit')

broker = RabbitBroker(BrokerConnConfig.RABBITMQ_URL, max_consumers=20)
app = FastStream(broker)

# asyncio.get_event_loop().run_until_complete(broker.connect())
#
# asyncio.get_event_loop().run_until_complete(broker.start())

def get_broker(max_consumers=None):
    return RabbitBroker(BrokerConnConfig.RABBITMQ_URL, max_consumers=max_consumers)