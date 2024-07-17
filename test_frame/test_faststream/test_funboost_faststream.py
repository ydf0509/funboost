import asyncio
import time

import anyio

import nb_log
from funboost import BoosterParams,BrokerEnum
from funboost.assist.faststream_helper import app,broker,get_broker
from funboost.consumers.faststream_consumer import FastStreamConsumer
from funboost.publishers.faststream_publisher import FastStreamPublisher
import faststream

# from pydantic_settings import BaseSettings

from faststream.rabbit.subscriber.asyncapi import AsyncAPISubscriber

nb_log.get_logger('faststream')
@BoosterParams(queue_name='test_funboost_faststream_queue',broker_kind=BrokerEnum.EMPTY,
               consumer_override_cls=FastStreamConsumer,publisher_override_cls=FastStreamPublisher)
async def f1(x,y):
    print(x,y)
    await asyncio.sleep(10)
    return x+y


@BoosterParams(queue_name='test_funboost_faststream_queue2',broker_kind=BrokerEnum.EMPTY,
               consumer_override_cls=FastStreamConsumer,publisher_override_cls=FastStreamPublisher)
def f2(x,y):
    print(x,y)
    time.sleep(10)
    return x-y

@BoosterParams(queue_name='test_funboost_faststream_queue3',broker_kind=BrokerEnum.EMPTY,
               consumer_override_cls=FastStreamConsumer,publisher_override_cls=FastStreamPublisher)
def f3(x,y):
    print(x,y)
    time.sleep(10)
    return x-y


if __name__ == '__main__':
    # anyio.run(app.run)

    f1.consume()
    f2.consume()
    f3.consume()

    for i in range(100000000):
        f1.push(1, 0)
        f2.push(2, 0)
        f3.push(3, 0)
        time.sleep(0.1)
    # asyncio.get_event_loop().run_until_complete(app.run())
    # print(type(f1.consumer.fast_stream_subscriber),f1.consumer.fast_stream_subscriber)
    #
    # asyncio.get_event_loop().run_until_complete(subc_start())
    #
    #
    # # asyncio.new_event_loop().run_until_complete(f1.consumer.fast_stream_subscriber.start())
    # # AsyncAPISubscriber.start()
    # # asyncio.get_event_loop().run_until_complete(broker.start())
    # asyncio.get_event_loop().run_forever()

    print(99999999999)

    while 1:
        time.sleep(1000)