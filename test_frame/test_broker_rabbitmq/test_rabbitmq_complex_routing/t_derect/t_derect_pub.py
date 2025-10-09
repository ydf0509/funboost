
from funboost import BoostersManager, PublisherParams, BrokerEnum, PriorityConsumingControlConfig

BROKER_KIND_FOR_TEST = BrokerEnum.RABBITMQ_COMPLEX_ROUTING
EXCHANGE_NAME = 'direct_log_exchange'



if __name__ == '__main__':
    # 优化点：获取一个通用的发布者，它的目标是交换机，而不是任何特定的队列。
    # 这里的 queue_name 仅用于生成发布者实例，实际发布时会被动态路由键覆盖。
    common_publisher = BoostersManager.get_cross_project_publisher(PublisherParams(
        queue_name='common_publisher_for_direct_exchange', 
        broker_kind=BROKER_KIND_FOR_TEST,
        broker_exclusive_config={
            'exchange_name': EXCHANGE_NAME,
            'exchange_type': 'direct',
            # 发布者不需要关心绑定键，但可以设置一个默认的发布路由键（如果需要）
            # 'routing_key_for_publish': 'info'
        }
    ))

    for i in range(10):
        # 发布一条 info 消息，指定路由键为 'info'，只有 info_fun 会收到
        common_publisher.publish({'msg': f'这是一条普通的INFO消息 {i}'},
                                 priority_control_config=PriorityConsumingControlConfig(
                                     other_extra_params={'routing_key_for_publish': 'info'}))

        # 发布一条 error 消息，指定路由键为 'error'，只有 error_fun 会收到
        common_publisher.publish({'msg': f'这是一条严重的ERROR消息 {i}'},
                                 priority_control_config=PriorityConsumingControlConfig(
                                     other_extra_params={'routing_key_for_publish': 'error'}))
