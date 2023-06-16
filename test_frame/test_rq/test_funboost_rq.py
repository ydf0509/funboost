import time

from funboost import boost, BrokerEnum,set_interrupt_signal_handler

from funboost.assist.rq_helper import RqHelper


@boost('test_rq_queue1a', broker_kind=BrokerEnum.RQ)
def f(x, y):
    time.sleep(2)
    print(f'x:{x},y:{y}')


@boost('test_rq_queue2a', broker_kind=BrokerEnum.RQ)
def f2(a, b):
    time.sleep(3)
    print(f'a:{a},b:{b}')


if __name__ == '__main__':
    RqHelper.add_nb_log_handler_to_rq()  # 使用nb_log日志handler来代替rq的
    for i in range(100):
        f.push(i, i * 2)
        f2.push(i, i * 10)
    f.consume()  # f.consume()是登记要启动的rq f函数的 queue名字,
    f2.consume()  # f2.consume()是登记要启动的rq f2函数的queue名字
    RqHelper.realy_start_rq_worker()  # realy_start_rq_worker 是真正启动rqworker，相当于命令行执行了 rqworker 命令。


