import asyncio
import logging

from funboost import BoosterParamsComplete
from funboost.concurrent_pool import FunboostBaseConcurrentPool, FlexibleThreadPool


class BoosterParamsMy(BoosterParamsComplete):
    log_level: int = logging.DEBUG
