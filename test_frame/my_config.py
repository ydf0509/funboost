import asyncio

from funboost import BoosterParamsComplete
from funboost.concurrent_pool import FunboostBaseConcurrentPool, FlexibleThreadPool


class BoosterParamsMy(BoosterParamsComplete):
    specify_concurrent_pool: FunboostBaseConcurrentPool = FlexibleThreadPool(1000)
    # specify_async_loop:asyncio.AbstractEventLoop = asyncio.get_event_loop()
