import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

loop = asyncio.new_event_loop()
cleint = AsyncIOMotorClient(mongo_collection_string,io_loop=loop)

# 把这个loop传给@boost装饰器的 specify_async_loop
# =loop