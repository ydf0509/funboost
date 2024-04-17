from funboost import BoosterParams, BoostersManager, ConcurrentModeEnum, BrokerEnum
from test_frame.test_distributed_turn_run.run_distribute_msg import gen_queue_name_by_ip, execute_msg_on_host, get_current_ip

booster = BoostersManager.build_booster(BoosterParams(queue_name=gen_queue_name_by_ip('queue2', get_current_ip('192.168.1.101x')),
                                                      concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
                                                      is_using_rpc_mode=True,
                                                      broker_kind=BrokerEnum.REDIS,
                                                      consuming_function=execute_msg_on_host,
                                                      ))


if __name__ == '__main__':
    booster.consume()
