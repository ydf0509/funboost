from datetime import datetime, timedelta
from traceback import format_tb
import logging
import sys

from pytz import utc
import six

import apscheduler

from apscheduler.events import (
    JobExecutionEvent, EVENT_JOB_MISSED, EVENT_JOB_ERROR, EVENT_JOB_EXECUTED)


def my_run_job(job, jobstore_alias, run_times, logger_name):
    """
    主要是把函数的入参放到event上，便于listener获取函数对象和函数入参。
    """

    """
    Called by executors to run the job. Returns a list of scheduler events to be dispatched by the
    scheduler.

    """
    events = []
    logger = logging.getLogger(logger_name)
    for run_time in run_times:
        # See if the job missed its run time window, and handle
        # possible misfires accordingly
        # print(job.misfire_grace_time) # add_job不设置时候默认为1秒。
        if job.misfire_grace_time is not None:
            # print(job,dir(job),job.args,job.kwargs)
            difference = datetime.now(utc) - run_time
            grace_time = timedelta(seconds=job.misfire_grace_time)
            if difference > grace_time:
                ev = JobExecutionEvent(EVENT_JOB_MISSED, job.id, jobstore_alias,
                                       run_time)
                ev.function_args = job.args
                ev.function_kwargs = job.kwargs
                ev.function = job.func

                events.append(ev)
                logger.warning('Run time of job "%s" was missed by %s', job, difference)
                continue

        logger.info('Running job "%s" (scheduled at %s)', job, run_time)
        try:
            retval = job.func(*job.args, **job.kwargs)
        except BaseException:
            exc, tb = sys.exc_info()[1:]
            formatted_tb = ''.join(format_tb(tb))

            ev = JobExecutionEvent(EVENT_JOB_ERROR, job.id, jobstore_alias, run_time,
                                   exception=exc, traceback=formatted_tb)
            ev.function_args = job.args
            ev.function_kwargs = job.kwargs
            ev.function = job.func

            events.append(ev)
            logger.exception('Job "%s" raised an exception', job)

            # This is to prevent cyclic references that would lead to memory leaks
            if six.PY2:
                sys.exc_clear()
                del tb
            else:
                import traceback
                traceback.clear_frames(tb)
                del tb
        else:
            ev = JobExecutionEvent(EVENT_JOB_EXECUTED, job.id, jobstore_alias, run_time,
                                   retval=retval)
            ev.function_args = job.args
            ev.function_kwargs = job.kwargs
            ev.function = job.func

            events.append(ev)
            logger.info('Job "%s" executed successfully', job)

    return events





def patch_run_job():
    # from apscheduler.executors import base
    # base.run_job = my_run_job
    apscheduler.executors.base.run_job = my_run_job
    apscheduler.executors.pool.run_job = my_run_job
