import functools

from nb_log import CompatibleLogger


@functools.lru_cache()
def _import_get_current_taskid():
    from funboost.core.current_task import get_current_taskid
    return get_current_taskid


class TaskIdLogger(CompatibleLogger):
    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False):
        extra = extra or {}
        if 'task_id' not in extra:
            extra['task_id'] = _import_get_current_taskid()()
        extra['sys_getframe_n'] = 3
        super()._log(level, msg, args, exc_info, extra, stack_info)
