
"""
Funboost 最最基础示例
演示如何使用 @boost 装饰器创建分布式任务队列
"""
import time
from funboost import boost, BrokerEnum, BoosterParams,ctrl_c_recv
import random
import nb_log
import threading



# 示例1: 最简单的任务函数
@boost(BoosterParams(
    queue_name="demo_queue_2b2",
    broker_kind=BrokerEnum.SQLITE_QUEUE,  # 使用 SQLite 作为消息队列，无需额外安装中间件
    qps=5,  # 每秒执行5次
    concurrent_num=1,  # 并发数为10
))
def add_task(x, y):
    """简单的加法任务"""
    print(f'计算: {x} + {y} = {x + y}')
    time.sleep(1)  # 模拟耗时操作
    if random.random() < 0.5:
        raise Exception('随机异常')
    return x + y


def test_thread():
    while True:
        time.sleep(10)
        print('test_thread')
        nb_log.debug('debug')
        nb_log.info('info')
        nb_log.warning('''warning
        warning第1行
        warning第2行
        warning第3行
    
        ''')
        nb_log.error('''error
        err第1行
        err第2行
        err第3行
        ''')
        nb_log.critical('''critical
        critical第1行
        critical第2行
        critical第3行
        ''')


if __name__ == '__main__':
    for i in range(10):
        add_task.push(i, i * 2)
    add_task.consume()
    threading.Thread(target=test_thread).start()
    ctrl_c_recv()

