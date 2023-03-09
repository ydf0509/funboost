

from funboost.utils.auto_run_on_remote import run_current_script_on_remote
run_current_script_on_remote()
import asyncio

from funboost.utils.dependency_packages.aioredis_adapt_py311 import RedisError


class TimeoutError(asyncio.TimeoutError, RedisError):
    pass

try:
    import aioredis
except Exception as e:
    print(e)
    aioredis.exceptions.TimeoutError=TimeoutError


import aioredis


# from funboost.utils.dependency_packages import aioredis_adapt_py311
