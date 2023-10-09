import uuid

from funboost.timing_job.apscheduler_use_redis_store import funboost_background_scheduler_redis_store
from funs import f

funboost_background_scheduler_redis_store.start(paused=True)
funboost_background_scheduler_redis_store.add_job(f,'date',
                                                  run_date='2023-10-07 18:03:59',
                                                  kwargs={'x':3,'y':4,'runonce_uuid':str(uuid.uuid4())})