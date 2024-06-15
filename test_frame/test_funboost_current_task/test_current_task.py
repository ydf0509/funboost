import asyncio
import random
import time

from funboost import boost, FunctionResultStatusPersistanceConfig, BoosterParams, ConcurrentModeEnum
from funboost.core.current_task import funboost_current_task
from funboost.core.task_id_logger import TaskIdLogger
import nb_log
from funboost.funboost_config_deafult import FunboostCommonConfig
from nb_log import LogManager

LOG_FILENAME_QUEUE_FCT = 'queue_fct.log'
# 使用TaskIdLogger创建的日志配合带task_id的日志模板，每条日志会自动带上task_id，方便用户搜索日志，定位某一个任务id的所有日志。
task_id_logger = LogManager('namexx', logger_cls=TaskIdLogger).get_logger_and_add_handlers(
    log_filename='queue_fct.log',
    error_log_filename=nb_log.generate_error_file_name(LOG_FILENAME_QUEUE_FCT),
    formatter_template=FunboostCommonConfig.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER, )

# 如果不使用TaskIdLogger来创建logger还想使用task_id的日志模板,需要用户在打印日志时候手动传 extra={'task_id': fct.task_id}
common_logger = nb_log.get_logger('namexx2', formatter_template=FunboostCommonConfig.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER)


@boost(BoosterParams(queue_name='queue_test_fct', qps=2, concurrent_num=5, log_filename=LOG_FILENAME_QUEUE_FCT, function_timeout=20))
def f(a, b):
    fct = funboost_current_task()  # 线程/协程隔离级别的上下文

    # 以下的每一条日志都会自带task_id显示，方便用户串联起来排查问题。
    fct.logger.warning('如果不想亲自创建logger对象，可以使用fct.logger来记录日志，fct.logger是当前队列的消费者logger对象')
    task_id_logger.info(fct.function_result_status.task_id)  # 获取消息的任务id
    task_id_logger.debug(fct.function_result_status.run_times)  # 获取消息是第几次重试运行
    task_id_logger.info(fct.full_msg)  # 获取消息的完全体。出了a和b的值意外，还有发布时间 task_id等。
    task_id_logger.debug(fct.function_result_status.publish_time_str)  # 获取消息的发布时间
    task_id_logger.debug(fct.function_result_status.get_status_dict())  # 获取任务的信息，可以转成字典看。

    # 如果 用户不是使用TaskIdLogger插件的logger对象,那么要在模板中显示task_id,
    common_logger.debug('假设logger不是TaskIdLogger类型的,想使用带task_id的日志模板,那么需要使用extra={"task_id":fct.task_id}', extra={'task_id': fct.task_id})

    time.sleep(2)
    task_id_logger.debug(f'哈哈 a: {a}')
    task_id_logger.debug(f'哈哈 b: {b}')
    task_id_logger.info(a + b)
    if random.random() > 0.99:
        raise Exception(f'{a} {b} 模拟出错啦')

    return a + b


@boost(BoosterParams(queue_name='aio_queue_test_fct', qps=2, concurrent_num=5, log_filename=LOG_FILENAME_QUEUE_FCT, concurrent_mode=ConcurrentModeEnum.THREADING, function_timeout=20))
async def aiof(a, b):
    fct = funboost_current_task()  # 线程/协程隔离级别的上下文

    # 以下的每一条日志都会自带task_id显示，方便用户串联起来排查问题。
    fct.logger.warning('如果不想亲自创建logger对象，可以使用fct.logger来记录日志，fct.logger是当前队列的消费者logger对象')
    task_id_logger.info(fct.function_result_status.task_id)  # 获取消息的任务id
    task_id_logger.debug(fct.function_result_status.run_times)  # 获取消息是第几次重试运行
    task_id_logger.info(fct.full_msg)  # 获取消息的完全体。出了a和b的值意外，还有发布时间 task_id等。
    task_id_logger.debug(fct.function_result_status.publish_time_str)  # 获取消息的发布时间
    task_id_logger.debug(fct.function_result_status.get_status_dict())  # 获取任务的信息，可以转成字典看。

    # 如果 用户不是使用TaskIdLogger插件的logger对象,那么要在模板中显示task_id,
    common_logger.debug('假设logger不是TaskIdLogger类型的,想使用带task_id的日志模板,那么需要使用extra={"task_id":fct.task_id}', extra={'task_id': fct.task_id})

    await asyncio.sleep(1)
    task_id_logger.debug(f'哈哈 a: {a}')
    task_id_logger.debug(f'哈哈 b: {b}')
    task_id_logger.info(a + b)
    if random.random() > 0.99:
        raise Exception(f'{a} {b} 模拟出错啦')

    return a + b


if __name__ == '__main__':
    # f(5, 6)  # 可以直接调用

    for i in range(0, 2):
        time.sleep(0.1)
        f.push(i, b=i * 2)
        aiof.push(i * 10, i * 20)

        f.consume()
        aiof.consume()
