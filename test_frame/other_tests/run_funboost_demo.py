import os

import asyncio
import logging
from datetime import datetime, timedelta
from funboost import boost, BrokerEnum, BoosterParams, ConcurrentModeEnum
from funboost.concurrent_pool import FunboostBaseConcurrentPool, FlexibleThreadPool, ConcurrentPoolBuilder
from redis import asyncio as aioredis
from typing import Any


def create_redis_pool():
    redis_pool = aioredis.ConnectionPool.from_url('redis://127.0.0.1:6379/1', encoding="utf-8", decode_responses=True)
    return redis_pool


class BoosterGeneralParams(BoosterParams):
    broker_kind: str = BrokerEnum.RABBITMQ_AMQPSTORM
    concurrent_mode: Any = ConcurrentModeEnum.ASYNC
    qps: float = 1
    max_retry_times: int = 4
    # specify_concurrent_pool: str = FlexibleThreadPool(8),
    user_custom_record_process_info_func: Any = None


@boost(boost_params=BoosterGeneralParams(queue_name='func00'))
async def func00(name, second):
    await asyncio.sleep(second)
    now_time = datetime.now()

    r = aioredis.Redis(connection_pool=create_redis_pool())
    if await r.exists(f'{name}-time'):
        old_time = await r.get(f'{name}-time')
        await r.rpush(f'{name}-cost', f'{(now_time - datetime.strptime(old_time, "%Y-%m-%d %H:%M:%S.%f")).total_seconds():.3f}')
    await r.set(f'{name}-time', now_time.strftime('%Y-%m-%d %H:%M:%S.%f'))
    await r.close()

    print(os.getpid(),name, now_time)


from funboost import BoostersManager, BoosterParams, run_forever
from funboost.timing_job.apscheduler_use_redis_store import funboost_background_scheduler_redis_store

if __name__ == '__main__':
    funboost_background_scheduler_redis_store.start(paused=False)

    # for num in range(1, 8):
    #     funboost_background_scheduler_redis_store.add_push_job(func=func00, id=f'func0{num}', trigger='interval', kwargs={'name': f'func0{num}', 'second': 0.1 * num}, replace_existing=True, seconds=1)
    func00.push('name1',1)
    func00.multi_process_start(7)

    run_forever()
