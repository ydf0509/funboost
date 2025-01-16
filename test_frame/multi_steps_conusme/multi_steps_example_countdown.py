import time
from funboost.utils.ctrl_c_end import ctrl_c_recv

from funboost.core.func_params_model import PriorityConsumingControlConfig
from funboost import boost, BrokerEnum,ConcurrentModeEnum,BoosterParams,Booster,ctrl_c_recv

from logging_tree import printout

@BoosterParams(queue_name='queue_test_step1b', qps=0.5, broker_kind=BrokerEnum.REDIS_ACK_ABLE, concurrent_mode=ConcurrentModeEnum.THREADING)
def step1(x):
    print(f'x 的值是 {x}')
    time.sleep(10)
    step2.publish({'y':x*10},priority_control_config=PriorityConsumingControlConfig(countdown=5))


@Booster(BoosterParams(queue_name='queue_test_step2b', qps=3, broker_kind=BrokerEnum.REDIS_ACK_ABLE))
def step2(y):
    print(f'y 的值是 {y}')
    time.sleep(20)



if __name__ == '__main__':

    step1.push(2)
    printout()

    # step1.consume()
    # step2.consume()



    """
    step1.consume()
    step2.consume()
    启动consume()都是在子线程运行的，
    代码主线程会很快结束，只有子线程在运行，需要防止 RuntimeError: cannot schedule new futures after interpreter shutdown
    
    因为用户主线程很快结束了， 定时任务用的aps的 backgroubsheduler 类型， 用户如果用定时，就在代码最末尾加个阻止主线程退出就可以了。
    """
    # while 1: # 这一行是阻止主线程退出，解决RuntimeError: cannot schedule new futures after interpreter shutdown
    #     time.sleep(100)
    ctrl_c_recv()

