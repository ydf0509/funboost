from funboost import funboost_config_deafult
from vine.promises import promise
from kombu import Exchange, Queue
from kombu import Connection
from kombu.messaging import Producer
from kombu.transport.base import Message

from kombu import Exchange, Queue
from loguru import logger
import time


# amqp_uri = 'amqp://pon:pon@192.168.31.245:5672//'
amqp_uri = f'amqp://{funboost_config_deafult.RABBITMQ_USER}:{funboost_config_deafult.RABBITMQ_PASS}@127.0.0.1:{funboost_config_deafult.RABBITMQ_PORT}/{funboost_config_deafult.RABBITMQ_VIRTUAL_HOST}'

def declare_exchange(exchange: Exchange):
    with Connection(amqp_uri) as conn:
        with conn.channel() as channel:
            exchange.declare(channel=channel)


def declare_queue(queue: Queue):
    with Connection(amqp_uri) as conn:
        with conn.channel() as channel:
            queue.declare(channel=channel)


imdb_exchange = Exchange('imdb', type='fanout')
declare_exchange(exchange=imdb_exchange)

imdb_queue = Queue('imdb_refresh', imdb_exchange,
                   routing_key='to_refresh', durable=True)
declare_queue(queue=imdb_queue)


with Connection(amqp_uri) as conn:
    with conn.channel() as channel:
        started_at = time.time()
        message = Message(channel=channel, body='123456789')

        producer = Producer(
            channel,
            exchange=imdb_exchange
        )
        for _ in range(1000000):
            res = producer.publish(
                body=message.body,
                routing_key='to_refresh',
                headers=message.headers
            )
        ended_at = time.time()
        logger.debug(f'pay time {ended_at-started_at} s')
        # logger.debug(res)