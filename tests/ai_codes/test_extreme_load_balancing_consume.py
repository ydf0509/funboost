import logging
import time
from funboost import boost, BrokerEnum, BoosterParams, ctrl_c_recv, ConcurrentModeEnum

# 极端的消费负载均衡示例
@boost(BoosterParams(
    queue_name='test_extreme_load_balancing_queue',
    broker_kind=BrokerEnum.REDIS_ACK_ABLE, # 这里使用REDIS_ACK_ABLE作为示例，其他broker同理
    log_level=logging.INFO,
    
    # 关键点1: 设置并发模式为 SINGLE_THREAD
    # 这样不会使用线程池，也就没有线程池内部的缓冲队列
    concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
    
    # 关键点2: 设置 broker 专属配置 pull_msg_batch_size 为 1
    # 默认情况下很多 broker (如Redis) 会批量拉取 (例如100条) 到内存中
    # 设置为 1 确保每次只拉取一条消息，处理完再拉下一条
    broker_exclusive_config={'pull_msg_batch_size': 1},
))
def extreme_load_balancing_consumer(x):
    print(f"Consumer processing: {x}")
    time.sleep(1) # 模拟耗时任务

if __name__ == '__main__':
    # 启动消费
    extreme_load_balancing_consumer.consume()
    ctrl_c_recv()

