import asyncio
import pydantic
import anyio
from faststream import FastStream,Context
from faststream.annotations import Logger

from faststream.redis import RedisBroker, ListSub

import nb_log

broker = RedisBroker("redis://localhost:6379/2")
app = FastStream(broker)

publisher = broker.publisher("response-queue")


@broker.subscriber(list="test-queue")
@broker.publisher(list="response-queue")
async def handle22(msg, logger: Logger,message=Context(),

    broker=Context(),
    context=Context(),):
    # await publisher.publish("Response")
    # await broker.publish("Response!", "response-queue")

    nb_log.debug([message,type(message),broker,context])
    logger.info(msg)
    await asyncio.sleep(20)
    return "Response!"


# @broker.subscriber("response-queue")
async def handle_response(msg, logger: Logger):
    logger.info(f"Process response: {msg}")


@app.after_startup
async def test_publishing():
    for i in range(100):
        await broker.publish("Hello!", list="test-queue")



'''
python -m faststream run faststream3:app
'''

if __name__ == '__main__':
    anyio.run(app.run)