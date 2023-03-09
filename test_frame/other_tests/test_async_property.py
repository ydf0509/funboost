import time
import asyncio

class A():
    @property
    def x(self):
        time.sleep(2)
        return 100

    @property
    async def y(self):
        await asyncio.sleep(3)
        return 2000


async  def t():
    a= A()
    print(a.x)
    print(await a.y)

asyncio.get_event_loop().run_until_complete(t())