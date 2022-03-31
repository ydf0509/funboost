from funboost import get_consumer, BrokerEnum


def add(a, b):
    print(a + b)


# 非装饰器方式，多了一个入参，需要手动指定consuming_function入参的值。
consumer = get_consumer('queue_test_f01', consuming_function=add, qps=0.2, broker_kind=BrokerEnum.REDIS_ACK_ABLE)

if __name__ == '__main__':
    for i in range(10, 20):
        consumer.publisher_of_same_queue.publish(dict(a=i, b=i * 2))  # consumer.publisher_of_same_queue.publish 发布任务
    consumer.start_consuming_message()  # 使用consumer.start_consuming_message 消费任务