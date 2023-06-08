import time
import sys
import random

from funboost.utils import times
import rq
import rq.job
import rq.compat
import rq.worker

from rq.defaults import (DEFAULT_LOGGING_FORMAT, DEFAULT_LOGGING_DATE_FORMAT)


class WindowsWorker(rq.Worker):
    """
    An extension of the RQ worker class
    that works on Windows.

    Does not support task timeouts
    and will probably crash if the task goes badly,
    due to not using fork().
    """

    def __init__(self, *args, **kwargs):
        if kwargs.get('default_worker_ttl', None) is None:
            # Force a small worker_ttl,
            # Otherwise the process seems to hang somewhere within connection.lpop and
            # you can't kill the worker with Ctrl+C until the timeout expires (Ctrl+Break works, though).
            # The default timeout is 420, however, which is too long.
            kwargs['default_worker_ttl'] = 2
        super(WindowsWorker, self).__init__(*args, **kwargs)

    def work(self, burst=False, logging_level="INFO", date_format=DEFAULT_LOGGING_DATE_FORMAT,
             log_format=DEFAULT_LOGGING_FORMAT, max_jobs=None, with_scheduler=False):
        """Starts the work loop.

        Pops and performs all jobs on the current list of queues.  When all
        queues are empty, block and wait for new jobs to arrive on any of the
        queues, unless `burst` mode is enabled.

        The return value indicates whether any jobs were processed.
        """
        self.log.info('Using rq_win.WindowsWorker (experimental)')
        self.default_worker_ttl=2
        return super(WindowsWorker, self).work(
            burst=burst,
            logging_level=logging_level,
            date_format=date_format,
            log_format=log_format,
            max_jobs=max_jobs,
            with_scheduler=with_scheduler
        )


    def execute_job(self, job, queue):
        """Spawns a work horse to perform the actual work and passes it a job.
        The worker will wait for the work horse and make sure it executes
        within the given timeout bounds, or will end the work horse with
        SIGALRM.
        """
        self.main_work_horse(job, queue)

    def main_work_horse(self, job, queue):
        """This is the entry point of the newly spawned work horse."""
        # After fork()'ing, always assure we are generating random sequences
        # that are different from the worker.
        random.seed()

        self._is_horse = True

        success = self.perform_job(job, queue)

        self._is_horse = False

    def perform_job(self, job, queue, heartbeat_ttl=None):
        """Performs the actual work of a job.  Will/should only be called
        inside the work horse's process.
        """
        self.prepare_job_execution(job)

        self.procline('Processing %s from %s since %s' % (
            job.func_name,
            job.origin, time.time()))

        try:
            job.started_at = times.now()

            # I have DISABLED the time limit!
            rv = job.perform()

            # Pickle the result in the same try-except block since we need to
            # use the same exc handling when pickling fails
            job._result = rv
            job._status = rq.job.JobStatus.FINISHED
            job.ended_at = times.now()

            #
            # Using the code from Worker.handle_job_success
            #
            with self.connection.pipeline() as pipeline:
                pipeline.watch(job.dependents_key)
                queue.enqueue_dependents(job, pipeline=pipeline)

                self.set_current_job_id(None, pipeline=pipeline)
                self.increment_successful_job_count(pipeline=pipeline)

                result_ttl = job.get_result_ttl(self.default_result_ttl)
                if result_ttl != 0:
                    job.save(pipeline=pipeline, include_meta=False)

                job.cleanup(result_ttl, pipeline=pipeline,
                            remove_from_queue=False)

                pipeline.execute()

        except:
            # Use the public setter here, to immediately update Redis
            job.status = rq.job.JobStatus.FAILED
            self.handle_exception(job, *sys.exc_info())
            return False

        if rv is None:
            self.log.info('Job OK')
        else:
            self.log.info('Job OK, result = %s' % (rq.worker.yellow(rq.compat.text_type(rv)),))

        if result_ttl == 0:
            self.log.info('Result discarded immediately.')
        elif result_ttl > 0:
            self.log.info('Result is kept for %d seconds.' % result_ttl)
        else:
            self.log.warning('Result will never expire, clean up result key manually.')

        return True