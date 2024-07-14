import asyncio
import pydantic
import anyio
from faststream import FastStream,Context
from faststream.annotations import Logger

# from faststream.redis import RedisBroker, ListSub
from faststream.rabbit import RabbitBroker

import nb_log

RABBITMQ_USER = 'admin'
RABBITMQ_PASS = '372148'
RABBITMQ_HOST = '106.55.244.110'
RABBITMQ_PORT = 5672
RABBITMQ_VIRTUAL_HOST = ''  # my_host # 这个是rabbitmq的虚拟子host用户自己创建的，如果你想直接用rabbitmq的根host而不是使用虚拟子host，这里写 空字符串 即可。
RABBITMQ_URL = f'amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/{RABBITMQ_VIRTUAL_HOST}'

# broker = RedisBroker("redis://localhost:6379/2")
broker = RabbitBroker(RABBITMQ_URL,max_consumers=20)
app = FastStream(broker)

publisher = broker.publisher("response-queue")


@broker.subscriber("test-queue")
@broker.publisher("response-queue")
async def handle22(msg, logger: Logger,message=Context(),

    broker=Context(),
    context=Context(),):
    # await publisher.publish("Response")
    # await broker.publish("Response!", "response-queue")

    nb_log.debug([msg,message,type(message),broker,context])
    logger.info(msg)
    await asyncio.sleep(1)
    return "Response!"


# @broker.subscriber("response-queue")
async def handle_response(msg, logger: Logger):
    logger.info(f"Process response: {msg}")


# @app.after_startup
async def test_publishing():
    for i in range(1000):
        await broker.publish("Hello!", "test-queue")



'''
python -m faststream run faststream3:app
'''

if __name__ == '__main__':
    anyio.run(test_publishing)
    anyio.run(app.run)