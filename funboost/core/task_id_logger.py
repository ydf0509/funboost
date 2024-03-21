import functools

from nb_log import CompatibleLogger
from funboost.core.current_task import get_current_taskid


class TaskIdLogger(CompatibleLogger):
    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False):
        extra = extra or {}
        if 'task_id' not in extra:
            extra['task_id'] = get_current_taskid()
        extra['sys_getframe_n'] = 3
        super()._log(level, msg, args, exc_info, extra, stack_info)
