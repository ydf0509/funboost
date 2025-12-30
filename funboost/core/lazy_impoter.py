import abc

from funboost.utils.decorators import cached_method_result, singleton, SingletonBaseNew, SingletonBaseCustomInit, singleton_no_lock

"""
延迟导入
或者使用时候再pip安装
"""


class FunboostLazyImpoter(SingletonBaseNew):
    """
    延迟导入,避免需要互相导入.
    """

    @property
    @cached_method_result
    def BoostersManager(self):
        from funboost.core import booster
        return booster.BoostersManager

    @property
    @cached_method_result
    def boost(self):
        from funboost.core import  booster
        return booster.boost

    @property
    @cached_method_result
    def Booster(self):
        from funboost.core import booster
        return booster.Booster

    @property
    @cached_method_result
    def flogger(self):
        from funboost.core.loggers import flogger
        return flogger



    # @property
    # @cached_method_result
    # def get_current_taskid(self):
    #     from funboost.core.current_task import get_current_taskid
    #     return get_current_taskid


funboost_lazy_impoter = FunboostLazyImpoter()


# noinspection SpellCheckingInspection
@singleton
class GeventImporter:
    """
    避免提前导入
    import gevent
    from gevent import pool as gevent_pool
    from gevent import monkey
    from gevent.queue import JoinableQueue
    """

    def __init__(self):
        import gevent
        print('导入gevent')
        from gevent import pool as gevent_pool
        from gevent import monkey
        from gevent.queue import JoinableQueue
        self.gevent = gevent
        self.gevent_pool = gevent_pool
        self.monkey = monkey
        self.JoinableQueue = JoinableQueue


@singleton_no_lock
class EventletImporter:
    """
    避免提前导入
    from eventlet import greenpool, monkey_patch, patcher, Timeout
    """

    def __init__(self):
        from eventlet import greenpool, monkey_patch, patcher, Timeout
        print('导入eventlet')
        self.greenpool = greenpool
        self.monkey_patch = monkey_patch
        self.patcher = patcher
        self.Timeout = Timeout


@singleton_no_lock
class PeeweeImporter:
    def __init__(self):
        """pip install peewee == 3.17"""
        from peewee import ModelSelect, Model, BigAutoField, CharField, DateTimeField, MySQLDatabase
        from playhouse.shortcuts import model_to_dict, dict_to_model
        self.ModelSelect = ModelSelect
        self.Model = Model
        self.BigAutoField = BigAutoField
        self.CharField = CharField
        self.DateTimeField = DateTimeField
        self.MySQLDatabase = MySQLDatabase
        self.model_to_dict = model_to_dict
        self.dict_to_model = dict_to_model


@singleton_no_lock
class AioHttpImporter:

    def __init__(self):
        """pip install aiohttp==3.8.3"""
        from aiohttp import web
        from aiohttp.web_request import Request
        self.web = web
        self.Request = Request


@singleton_no_lock
class NatsImporter:
    def __init__(self):
        """pip install nats-python """
        from pynats import NATSClient, NATSMessage
        self.NATSClient = NATSClient
        self.NATSMessage = NATSMessage


@singleton_no_lock
class GnsqImporter:
    def __init__(self):
        """pip install  gnsq==1.0.1"""
        from gnsq import Consumer, Message
        from gnsq import Producer, NsqdHTTPClient
        from gnsq.errors import NSQHttpError
        self.Consumer = Consumer
        self.Message = Message
        self.Producer = Producer
        self.NsqdHTTPClient = NsqdHTTPClient
        self.NSQHttpError = NSQHttpError


@singleton_no_lock
class ElasticsearchImporter:
    def __init__(self):
        """pip install elasticsearch """
        from elasticsearch import helpers
        self.helpers = helpers


@singleton_no_lock
class PsutilImporter:
    def __init__(self):
        """pip install  psutil"""
        import psutil
        self.psutil = psutil


@singleton_no_lock
class PahoMqttImporter:
    def __init__(self):
        """pip install paho-mqtt"""
        import paho.mqtt.client as mqtt
        self.mqtt = mqtt


@singleton_no_lock
class ZmqImporter:
    def __init__(self):
        """pip install zmq pyzmq"""
        import zmq
        self.zmq = zmq


@singleton_no_lock
class KafkaPythonImporter:
    def __init__(self):
        """pip install kafka-python==2.0.2"""

        from kafka import KafkaConsumer as OfficialKafkaConsumer, KafkaProducer, KafkaAdminClient
        from kafka.admin import NewTopic
        from kafka.errors import TopicAlreadyExistsError

        self.OfficialKafkaConsumer = OfficialKafkaConsumer
        self.KafkaProducer = KafkaProducer
        self.KafkaAdminClient = KafkaAdminClient
        self.NewTopic = NewTopic
        self.TopicAlreadyExistsError = TopicAlreadyExistsError


if __name__ == '__main__':
    print()
    for i in range(1000000):
        # funboost_lazy_impoter.BoostersManager
        # EventletImporter().greenpool
        # GeventImporter().JoinableQueue
        ZmqImporter().zmq
    print()
