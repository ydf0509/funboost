import abc

from funboost.utils.decorators import cached_method_result, singleton, SingletonBaseNew, SingletonBaseCustomInit


# @singleton   # 不方便代码补全

class LazyImpoter(SingletonBaseNew):
    """
    延迟导入,避免需要互相导入.
    """

    @property
    @cached_method_result
    def BoostersManager(self):
        from funboost.core.booster import BoostersManager
        return BoostersManager

    # @property
    # @cached_method_result
    # def get_current_taskid(self):
    #     from funboost.core.current_task import get_current_taskid
    #     return get_current_taskid


lazy_impoter = LazyImpoter()


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

    @property
    @cached_method_result
    def gevent(self):
        import gevent
        print('导入gevent')
        return gevent

    @property
    @cached_method_result
    def gevent_pool(self):
        from gevent import pool as gevent_pool
        return gevent_pool

    @property
    @cached_method_result
    def monkey(self):
        from gevent import monkey
        print('导入gevent')
        return monkey

    @property
    @cached_method_result
    def JoinableQueue(self):
        from gevent.queue import JoinableQueue
        return JoinableQueue


@singleton
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

@singleton
class PeeweeImporter:
    def __init__(self):
        '''pip install peewee == 3.17'''
        from peewee import ModelSelect, Model, BigAutoField, CharField, DateTimeField, MySQLDatabase
        from playhouse.shortcuts import model_to_dict, dict_to_model
        self.ModelSelect = ModelSelect
        self.Model = Model
        self.BigAutoField = BigAutoField
        self.CharField = CharField
        self.DateTimeField =DateTimeField
        self.MySQLDatabase = MySQLDatabase
        self.model_to_dict = model_to_dict
        self.dict_to_model =dict_to_model

if __name__ == '__main__':
    for i in range(10000):
        # lazy_impoter.BoostersManager
        EventletImporter().greenpool
        GeventImporter().JoinableQueue
