from funboost import boost
from funboost.contrib.redis_consume_latest_msg_broker import BROKER_KIND_REDIS_CONSUME_LATEST

@boost('test_list_queue2', broker_kind=BROKER_KIND_REDIS_CONSUME_LATEST, qps=10, )
def f(x):
    print(x * 10)

if __name__ == '__main__':

    f.clear()
    for i in range(50):
        f.push(i)
    print(f.publisher.get_message_count())
    f.consume()