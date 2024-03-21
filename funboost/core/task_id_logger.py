import functools

from nb_log import CompatibleLogger
from funboost.core.current_task import get_current_taskid


class TaskIdLogger(CompatibleLogger):
    """
    如果你要使用带taskid的日志模板,一定要使用
     LogManager('namexx',logger_cls=TaskIdLogger).get_logger_and_add_handlers(....)
     的方式来创建logger, 就是需要指定logger_cls=TaskIdLogger ,否则的话你需要在打印日志时候 手动传递extra logger.info(msg,extra={'task_id':task_idxxx})
     """
    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False):
        extra = extra or {}
        if 'task_id' not in extra:
            extra['task_id'] = get_current_taskid()
        if 'sys_getframe_n' not in extra:
            extra['sys_getframe_n'] = 3
        super()._log(level, msg, args, exc_info, extra, stack_info)
