import time
import asyncio
from funboost import boost, BrokerEnum, ConcurrentModeEnum


@boost('test_queue_f1', broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM, qps=2, concurrent_mode=ConcurrentModeEnum.ASYNC)
async def f1(x, y):
    await asyncio.sleep(7)
    return x + y


@boost('test_queue_f2', broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM, qps=0.5)
def f2(a, b):
    time.sleep(5)
    return a - b


if __name__ == '__main__':
    f1.clear()
    for i in range(1000):
        f1.push(i, i * 2)
        f2.push(i, b=i * 2)

    # 在本机启动一个进程消费f1函数,每个进程内部是按照f1装饰器所指定的asyncio异步方式并发。
    f1.consume()

    # 在本机启动2个进程消费f1函数,每个进程内部是按照f2装饰器所指定的线程方式方式并发。(默认是线程并发。支持5种细粒度并发，包括多线程 asyncio gevent  eventlet 单线程 )
    f2.multi_process_consume(2)

    # 在虚拟机192.168.114.137启动一个进程消费f1函数,每个进程内部是按照f1装饰器所指定的asyncio异步方式并发。
    f1.fabric_deploy('192.168.114.137', 22, 'ydf', '123456')

    # 在腾讯云启动3个进程消费f2函数，,每个进程内部是按照f2装饰器所指定的线程方式方式并发。
    # file_volume_limit是限制100kb以上的不自动上传，only_upload_within_the_last_modify_time是限制值上传最近10天修改过的代码文件。
    f2.fabric_deploy('106.55.244.110', 22, 'root', '(H8{Q$%Bb2_|nSg}', sftp_log_level=10,
                     file_volume_limit=100 * 1000, only_upload_within_the_last_modify_time=10 * 24 * 3600,
                     process_num=3)
