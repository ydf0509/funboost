import time

from funboost import boost, BoostersManager, BoosterParams, ConcurrentModeEnum, BrokerEnum


def gen_queue_name_by_ip(queue_namex, ip):
    return queue_namex + '-' + ip.replace(".", "_")


def get_current_ip(ip=None):
    return ip  # 实际是写成自动获取当前机器的ip,不需要传参,作者例子现在是在一台机器2个脚本运行,模拟2台机器,所以需要传参.


ip_101 = '192.168.1.101b'
ip_102 = '192.168.1.102b'
ip_list = [ip_101, ip_102]


class GlobalVars:
    i = -1


@boost(BoosterParams(queue_name='queue1', concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD, broker_kind=BrokerEnum.REDIS))
def distribute_msg(x):
    """轮流分发消息到每台机器,并且阻塞等待函数运行完成,才分发下一个任务到下一台机器"""
    GlobalVars.i += 1
    ip = ip_list[GlobalVars.i % len(ip_list)]  # 轮流向每台机器的队列分发推送消息
    booster = build_booster_really_execute_msg_on_host_by_ip(ip)
    async_result = booster.push(x)
    # async_result.set_timeout(10)
    """
    使用async_result.get() rpc模式是为了阻塞,直到 execute_msg_on_host 函数运行消息完成,
    配合上distribute_msg是单线程并发模式, 这样就是保证了多台机器只有一个机器在使用 really_execute_msg_on_host 函数运行queue1中取出的消息
    """
    print(async_result.get())


def really_execute_msg_on_host(x):
    """真正的执行消息,在每台机器轮流运行这个函数."""
    time.sleep(5)
    print(x)
    return f'{x} finish from ip_xx '


def build_booster_really_execute_msg_on_host_by_ip(ip):
    return BoostersManager.build_booster(BoosterParams(queue_name=gen_queue_name_by_ip('queue2', ip),
                                                       concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
                                                       is_using_rpc_mode=True,
                                                       broker_kind=BrokerEnum.REDIS,
                                                       consuming_function=really_execute_msg_on_host,
                                                       ))


if __name__ == '__main__':
    distribute_msg.clear()
    for i in range(10):
        distribute_msg.push(i)
    distribute_msg.consume()
    """
    这个消息分发部署在一台机器上
    """