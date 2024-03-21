from funboost.utils.decorators import cached_method_result


class LazyImpoter:
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


if __name__ == '__main__':
    for i in range(10000):
        LazyImpoter().BoostersManager
        LazyImpoter().BoostersManager
