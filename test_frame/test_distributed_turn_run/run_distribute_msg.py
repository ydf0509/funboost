import time

from funboost import boost,BoostersManager,BoosterParams,ConcurrentModeEnum,BrokerEnum

def gen_queue_name_by_ip(queue_namex,ip):
    return queue_namex + '-' + ip.replace(".","_")

def get_current_ip(ip=None):
    return ip  # 实际是写成自动获取当前机器的ip,不需要传参,作者例子现在是在一台机器2个脚本运行,模拟2台机器,所以需要传参.


ip_list= ['192.168.1.101x','192.168.1.102x',]
class GlobalVars:
    i = -1

@boost(BoosterParams(queue_name='queue1',concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,broker_kind=BrokerEnum.REDIS))
def distribute_msg(x):
    GlobalVars.i += 1
    ip = ip_list[GlobalVars.i % len(ip_list)] # 轮流向每台机器的队列推送消息
    booster = BoostersManager.build_booster(BoosterParams(queue_name=gen_queue_name_by_ip('queue2',ip),
                                                concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
                                                is_using_rpc_mode=True,
                                                broker_kind=BrokerEnum.REDIS,
                                                consuming_function=execute_msg_on_host,
                                                ))
    async_result= booster.push(x)
    # async_result.set_timeout(10)
    print(async_result.get())   # 使用async_result.get() rpc模式是为了阻塞,直到execute_msg_on_host函数运行消息完成,这样就是保证了多台机器只有一个机器在运行queue1中取出的消息


def execute_msg_on_host(x):
    time.sleep(5)
    print(x)
    return f'{x} finish from ip_xx '


if __name__ == '__main__':
    distribute_msg.clear()
    for i in range(10):
        distribute_msg.push(i)
    distribute_msg.consume()