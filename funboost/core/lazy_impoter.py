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
    import gevent
    from gevent import pool as gevent_pool
    from gevent import monkey
    from gevent.queue import JoinableQueue
    """

    @property
    @cached_method_result
    def gevent(self):
        import gevent
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
        return monkey

    @property
    @cached_method_result
    def JoinableQueue(self):
        from gevent.queue import JoinableQueue
        return JoinableQueue


@singleton
class EventletImporter:
    """
    from eventlet import greenpool, monkey_patch, patcher, Timeout
    """

    def __init__(self):
        from eventlet import greenpool, monkey_patch, patcher, Timeout
        print('导入gevent')
        self.greenpool = greenpool
        self.monkey_patch = monkey_patch
        self.patcher = patcher
        self.Timeout = Timeout


if __name__ == '__main__':
    for i in range(10000):
        # lazy_impoter.BoostersManager
        EventletImporter().greenpool
        GeventImporter().JoinableQueue
