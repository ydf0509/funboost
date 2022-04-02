
import os
import time

from datetime import datetime

import pymongo
from unittest import TestCase

from .mongomq import MongoQueue
from .lock import MongoLock, lock


class MongoLockTest(TestCase):

    def setUp(self):
        self.client = pymongo.Connection(os.environ.get("TEST_MONGODB"))
        self.db = self.client.test_queue
        self.collection = self.db.locks

    def tearDown(self):
        self.client.drop_database("test_queue")

    def test_lock_acquire_release_context_manager(self):
        with lock(self.collection, 'test1') as l:
            self.assertTrue(l.locked)
        self.assertEqual(self.collection.find().count(), 0)

    def test_auto_expires_old(self):
        lock = MongoLock(self.collection, 'test2', lease=2)
        self.assertTrue(lock.acquire())

        time.sleep(2.2)
        # Reports truthfully it doesn't have the local anymore,
        # using ttl time, stale db record extant.
        self.assertFalse(lock.locked)

        lock2 = MongoLock(self.collection, 'test2')
        # New lock acquire will take ownership based on old ttl\
        self.assertTrue(lock2.acquire())

        # Releasing the original doesn't change ownership
        self.assertTrue(lock.release())
        records = list(self.collection.find())
        self.assertEqual(len(records), 1)

        self.assertEqual(records.pop()['client_id'], lock2.client_id)
        self.assertFalse(lock.acquire(wait=False))

        lock2.release()
        self.assertFalse(list(self.collection.find()))


class MongoQueueTest(TestCase):

    def setUp(self):
        self.client = pymongo.Connection(os.environ.get("TEST_MONGODB"))
        self.db = self.client.test_queue
        self.queue = MongoQueue(self.db.queue_1, "consumer_1")

    def tearDown(self):
        self.client.drop_database("test_queue")

    def assert_job_equal(self, job, data):
        for k, v in data.items():
            self.assertEqual(job.payload[k], v)

    def test_put_next(self):
        data = {"context_id": "alpha",
                "data": [1, 2, 3],
                "more-data": time.time()}
        self.queue.put(dict(data))
        job = self.queue.next()
        self.assert_job_equal(job, data)

    def test_get_empty_queue(self):
        job = self.queue.next()
        self.assertEqual(job, None)

    def test_priority(self):
        self.queue.put({"name": "alice"}, priority=1)
        self.queue.put({"name": "bob"}, priority=2)
        self.queue.put({"name": "mike"}, priority=0)

        self.assertEqual(
            ["bob", "alice", "mike"],
            [self.queue.next().payload['name'],
             self.queue.next().payload['name'],
             self.queue.next().payload['name']])

    def test_complete(self):
        data = {"context_id": "alpha",
                "data": [1, 2, 3],
                "more-data": datetime.now()}

        self.queue.put(data)
        self.assertEqual(self.queue.size(), 1)
        job = self.queue.next()
        job.complete()
        self.assertEqual(self.queue.size(), 0)

    def test_release(self):
        data = {"context_id": "alpha",
                "data": [1, 2, 3],
                "more-data": time.time()}

        self.queue.put(data)
        job = self.queue.next()
        job.release()
        self.assertEqual(self.queue.size(), 1)
        job = self.queue.next()
        self.assert_job_equal(job, data)

    def test_error(self):
        pass

    def test_progress(self):
        pass

    def test_stats(self):

        for i in range(5):
            data = {"context_id": "alpha",
                    "data": [1, 2, 3],
                    "more-data": time.time()}
            self.queue.put(data)
        job = self.queue.next()
        job.error("problem")

        stats = self.queue.stats()
        self.assertEqual({'available': 5,
                          'total': 5,
                          'locked': 0,
                          'errors': 0}, stats)

    def test_context_manager_error(self):
        self.queue.put({"foobar": 1})
        job = self.queue.next()
        try:
            with job as data:
                self.assertEqual(data['payload']["foobar"], 1)
                # Item is returned to the queue on error
                raise SyntaxError
        except SyntaxError:
            pass

        job = self.queue.next()
        self.assertEqual(job.data['attempts'], 1)

    def test_context_manager_complete(self):
        self.queue.put({"foobar": 1})
        job = self.queue.next()
        with job as data:
            self.assertEqual(data['payload']["foobar"], 1)
        job = self.queue.next()
        self.assertEqual(job, None)
