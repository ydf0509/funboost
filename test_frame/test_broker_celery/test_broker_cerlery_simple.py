
"""
此脚本演示 funboost 使用 celery 作为broker,
但用户除了使用funboost的统一化api,任然可以使用 celery 底层的细节.
"""
import time
from funboost import boost, BrokerEnum,BoosterParams
from funboost.assist.celery_helper import CeleryHelper,Task

@boost(BoosterParams(queue_name='test_broker_celery_simple',
                     broker_kind=BrokerEnum.CELERY, # 使用 celery 框架整体作为 funboost的broker
                     concurrent_num=10,))
def my_fun(x, y):
    time.sleep(3)
    print(6666, x, y)
    return x + y

if __name__ == '__main__':
    # funboost 语法来发布消息,my_fun 类型是 funboost的 Booster
    my_fun.push(1,2)

    #  用户可以通过my_fun.consumer.celery_task ,使用celery自带delay来发布消息
    # my_fun.consumer.celery_task 类型是 celery的 celery.app.task.Task
    my_fun_celery_task : Task = my_fun.consumer.celery_task
    my_fun_celery_task.delay(3,4) # 可以用 celery task 原生delay
    my_fun_celery_task.apply_async(args=[5,6],task_id='123456789123',countdown=10)  # 可以用 celery task 原生 apply_async

    my_fun.consume()  # 这个不是立即启动消费,是登记celery要启动的queue
    CeleryHelper.realy_start_celery_worker() # 这个是真的启动celery worker 命令行来把所有已登记的queue启动消费
