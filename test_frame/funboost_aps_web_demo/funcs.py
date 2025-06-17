from funboost import  BrokerEnum,BoosterParams

@BoosterParams(queue_name='sum_queue4', broker_kind=BrokerEnum.REDIS_ACK_ABLE)
def fun_sum(x,y):
    print(f'fun1: {x} + {y} = {x+y}')



