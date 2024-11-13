import requests
from amqp import Message, Connection, ConnectionError, ChannelError
import nb_log
TEST_QUEUE = 'pyrabbit.testq'

connection = Connection(host='localhost:5672', userid='guest',
                             password='guest', virtual_host='/')
channel = connection.channel()
channel.queue_delete(TEST_QUEUE)

channel.exchange_declare(TEST_QUEUE, 'direct')
x = channel.queue_declare(TEST_QUEUE)
        # self.assertEqual(x.message_count, x[1])
        # self.assertEqual(x.consumer_count, x[2])
        # self.assertEqual(x.queue, TEST_QUEUE)
channel.queue_bind(TEST_QUEUE, TEST_QUEUE, TEST_QUEUE)