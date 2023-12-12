import logging
import time
from funboost import boost, BrokerEnum, BoosterParams
from nb_log import get_logger

LOG_FILENAME = '自定义日志文件名.log'


class BoosterParamsMy(BoosterParams):  # 传这个类就可以少每次都亲自指定使用rabbitmq作为消息队列，和使用rpc模式。
    """
    定义子类时候，字段也要注意带上类型注释
    """
    broker_kind: str = BrokerEnum.RABBITMQ
    max_retry_times: int = 4
    log_level: int = logging.DEBUG
    log_filename: str = LOG_FILENAME
    # fdfd:int =4

my_file_logger = get_logger('my_business', log_filename=LOG_FILENAME)


@boost(boost_params=BoosterParamsMy(queue_name='task_queue_name1111', qps=3, ))
def task_fun(x, y):
    print(f'{x} + {y} = {x + y}')
    my_file_logger.debug(f"1111 这条日志会写到 {LOG_FILENAME} 日志文件中  {x} + {y} = {x + y}")
    time.sleep(3)  # 框架会自动并发绕开这个阻塞，无论函数内部随机耗时多久都能自动调节并发达到每秒运行 3 次 这个 task_fun 函数的目的。


@boost(boost_params=BoosterParamsMy(queue_name='task_queue_name2222', qps=10, ))
def task_fun2(x, y):
    print(f'{x} - {y} = {x - y}')
    my_file_logger.debug(f"2222 这条日志会写到 {LOG_FILENAME} 日志文件中 {x} - {y} = {x - y} ")
    time.sleep(3)  # 框架会自动并发绕开这个阻塞，无论函数内部随机耗时多久都能自动调节并发达到每秒运行 10 次 这个 task_fun 函数的目的。


if __name__ == "__main__":
    task_fun.consume()  # 消费者启动循环调度并发消费任务
    task_fun2.consume()
    for i in range(10):
        task_fun.push(i, y=i * 2)  # 发布者发布任务
        task_fun2.push(i, i * 10)
