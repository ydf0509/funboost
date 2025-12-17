

import time
from funboost import boost, BrokerEnum, BoosterParams

# 1. 为你的函数加上 @boost 装饰器
@boost(BoosterParams(queue_name="hello_queue", qps=5, broker_kind=BrokerEnum.SQLITE_QUEUE))
def say_hello(name: str):
    print(f"Hello, {name}!")
    time.sleep(1)

if __name__ == "__main__":
    # 2. 发布任务并启动消费
    for i in range(50):
        say_hello.push(name=f"Funboost User {i}")
    
    say_hello.consume()