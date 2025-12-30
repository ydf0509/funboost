from tests.ai_codes.test_extreme_load_balancing_consume import extreme_load_balancing_consumer

if __name__ == '__main__':
    print("开始发布消息...")
    for i in range(50):
        extreme_load_balancing_consumer.push(i)
    print("消息发布完成，请启动两个或多个 consumer 进程来观察负载均衡效果。")

