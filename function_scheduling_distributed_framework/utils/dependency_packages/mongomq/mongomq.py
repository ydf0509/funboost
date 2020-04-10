import pymongo
import traceback

from datetime import datetime, timedelta

from pymongo import ReturnDocument

from .utils import enum


JobStatus = enum(
    'JobStatus',
    QUEUED='queued',
    FINISHED='finished',
    FAILED='failed',
    STARTED='started'
)


DEFAULT_INSERT = {
    "attempts": 0,
    "locked_by": None,
    "locked_at": None,
    "last_error": None
}


class MongoQueue(object):
    """
    A queue class
    """

    def __init__(self, collection, consumer_id, timeout=300, max_attempts=3,
                 ttl=18000):
        self.collection = collection
        self.consumer_id = consumer_id
        self.timeout = timeout
        self.ttl = ttl
        self.max_attempts = max_attempts
        self.create_ttl_index()

    def create_ttl_index(self):
        try:
            self.collection.create_index(
                "created_at", name='exp_created_at_idx',
                expireAfterSeconds=self.ttl
            )
        except pymongo.errors.OperationFailure:
            self.collection.drop_index("exp_created_at_idx")
            self.collection.create_index(
                "created_at", name='exp_created_at_idx',
                expireAfterSeconds=self.ttl
            )

    def close(self):
        """
        Close the in memory queue connection.
        """
        self.collection.connection.close()

    def clear(self):
        """
        Clear the queue.
        """
        return self.collection.drop()

    def size(self):
        """
        Total size of the queue
        """
        return self.collection.count()

    def repair(self):
        """
        Clear out stale locks.

        Increments per job attempt counter.
        """
        self.collection.find_and_modify(
            query={
                "locked_by": {"$ne": None},
                "locked_at": {
                    "$lt": datetime.now() - timedelta(self.timeout)}},
            update={
                "$set": {"locked_by": None, "locked_at": None},
                "$inc": {"attempts": 1}}
        )

    def drop_max_attempts(self):
        self.collection.find_and_modify(
            {"attempts": {"$gte": self.max_attempts}},
            remove=True)

    def put(self, payload, priority=0):
        """
        Place a job into the queue
        """
        job = dict(DEFAULT_INSERT)
        job['priority'] = priority
        job['payload'] = payload
        job['created_at'] = datetime.utcnow()
        job['finished_at'] = None
        job['status'] = JobStatus.QUEUED
        return self.collection.insert(job)

    def next(self):
        """
        Get next job from queue
        """
        return self._wrap_one(self.collection.find_and_modify(
            query={"locked_by": None,
                   "locked_at": None,
                   "attempts": {"$lt": self.max_attempts},
                   "status": {
                       "$eq": JobStatus.QUEUED}
                   },
            update={
                "$set": {
                    "locked_by": self.consumer_id,
                    "locked_at": datetime.now(),
                    'status': JobStatus.STARTED
                }
            },
            sort=[('priority', pymongo.DESCENDING)],
            new=1,
            limit=1
        ))

    def _jobs(self):
        return self.collection.find(
            query={"locked_by": None,
                   "locked_at": None,
                   "attempts": {"$lt": self.max_attempts}},
            sort=[('priority', pymongo.DESCENDING)],
        )

    def _wrap_one(self, data):
        return data and Job(self, data) or None

    def stats(self):
        """Get statistics on the queue.

        Use sparingly requires a collection lock.
        """

        js = """function queue_stat(){
        return db.eval(
        function(){
           var a = db.%(collection)s.count(
               {'locked_by': null,
                'attempts': {$lt: %(max_attempts)i}});
           var l = db.%(collection)s.count({'locked_by': /.*/});
           var e = db.%(collection)s.count(
               {'attempts': {$gte: %(max_attempts)i}});
           var t = db.%(collection)s.count();
           return [a, l, e, t];
           })}""" % {
             "collection": self.collection.name,
             "max_attempts": self.max_attempts}

        return dict(zip(
            ["available", "locked", "errors", "total"],
            self.collection.database.eval(js)))


class Job(object):

    def __init__(self, queue, data):
        """
        :param queue: MongoQueue
        :param data: dict
        """
        self._queue = queue
        self._data = data

    @property
    def payload(self):
        return self._data['payload']

    @property
    def status(self):
        return self._data['status']

    @property
    def job_id(self):
        return self._data["_id"]

    @property
    def priority(self):
        return self._data["priority"]

    @property
    def attempts(self):
        return self._data["attempts"]

    @property
    def locked_by(self):
        return self._data["locked_by"]

    @property
    def locked_at(self):
        return self._data["locked_at"]

    @property
    def last_error(self):
        return self._data["last_error"]

    @property
    def finished_at(self):
        return self._data["finished_at"]

    @property
    def created_at(self):
        return self._data["created_at"]

    def complete(self):
        """
        Job has been completed.
        """
        self._data = self._queue.collection.find_one_and_update(
            {"_id": self.job_id, "locked_by": self._queue.consumer_id},
            update={
                "$set": {
                    'status': JobStatus.FINISHED, 'finished_at': datetime.now()
                }
            },
            return_document=ReturnDocument.AFTER
        )

    def error(self, message=None):
        """
        Note an error processing a job, and return it to the queue.
        """
        self._data = self._queue.collection.find_one_and_update(
            {"_id": self.job_id, "locked_by": self._queue.consumer_id},
            update={"$set": {
                "locked_by": None, "locked_at": None, "last_error": message,
                'status': JobStatus.FAILED
            },
                "$inc": {"attempts": 1}},
            return_document=ReturnDocument.AFTER)

    def progress(self, count=0):
        """
        Note progress on a long running task.
        """
        self._data = self._queue.collection.find_one_and_update(
            {"_id": self.job_id, "locked_by": self._queue.consumer_id},
            update={"$set": {"progress": count, "locked_at": datetime.now()}},
            return_document=ReturnDocument.AFTER)

    def release(self):
        """
        Put the job back into_queue.
        """
        self._data = self._queue.collection.find_one_and_update(
            {"_id": self.job_id, "locked_by": self._queue.consumer_id},
            update={"$set": {"locked_by": None, "locked_at": None,
                             'status': JobStatus.QUEUED},
                    "$inc": {"attempts": 1}},
            return_document=ReturnDocument.AFTER)

    def __enter__(self):
        return self._data

    def __exit__(self, type, value, tb):
        if (type, value, tb) == (None, None, None):
            self.complete()
        else:
            error = traceback.format_exc()
            self.error(error)
