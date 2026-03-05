
"""
此脚本演示 funboost 使用 celery 作为broker,
但用户除了使用funboost的统一化api,任然可以使用 celery 底层的细节.
"""
import time


from funboost import boost, BrokerEnum,BoosterParams
from funboost.assist.celery_helper import CeleryHelper,Task

@boost(BoosterParams(queue_name='test_broker_celery_retry3',
                     broker_kind=BrokerEnum.CELERY, # 使用 celery 框架整体作为 funboost的broker
                     concurrent_num=10,
                    
                    max_retry_times=100,
                      is_using_advanced_retry=True,
                        advanced_retry_config={
                            'retry_mode': 'requeue',          # 延迟重新入队，不耗工作线程
                            'retry_base_interval': 10.0,       # 初始 10s
                            'retry_multiplier': 2.0,          # 每次翻倍：10s -> 20s -> 40s ...
                            'retry_max_interval': 300.0,      # 重试间隔最高等待 5 分钟，不会无限制往上翻倍
                            'retry_jitter': False,            # 是否添加随机抖动，随机乘以 0.5 - 1.5 倍数
                        },  

                     broker_exclusive_config= {
                        'celery_task_config' : dict(
                            # autoretry_for = (ZeroDivisionError,),
                            retry_kwargs={'max_retries': 50},                       # 最大重试次数
                            retry_backoff=10,                                   # 开启指数退避策略
                            retry_backoff_max=300,
                            retry_jitter=False,                                    # 增加随机抖动，防止波峰效应
                            default_retry_delay=60                                # 默认等待时间（秒）
                        )
                        }
                     
                     ))
def my_fun(x, y):
    1/ 0

if __name__ == '__main__':
    # funboost 语法来发布消息,my_fun 类型是 funboost的 Booster
    my_fun.clear()
    my_fun.push(1,2)

    
    my_fun.consume()  # 这个不是立即启动消费,是登记celery要启动的queue
    CeleryHelper.realy_start_celery_worker() # 这个是真的启动celery worker 命令行来把所有已登记的queue启动消费
