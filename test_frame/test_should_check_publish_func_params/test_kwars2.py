
"""
Funboost 消费任意 JSON 消息格式完整示例（兼容非 Funboost 发布）

Funboost 天然支持消费任意 JSON 消息，且不要求任务必须通过 Funboost 发布，具备极强的异构兼容性与消息格式容忍度，
这在实际系统中大大降低了对接成本与协作门槛。
相比之下，Celery 的格式封闭、消息结构复杂，使得跨语言对接几乎不可能，这一点 Funboost 完胜。
"""

import time
import redis
import json
from funboost import boost, BrokerEnum, BoosterParams, fct,ctrl_c_recv

@boost(boost_params=BoosterParams(queue_name="task_queue_name2c", qps=5,
                                   broker_kind=BrokerEnum.REDIS, 
                                  log_level=10, should_check_publish_func_params=False
                                  ))  # 入参包括20种，运行控制方式非常多，想得到的控制都会有。
def task_fun(**kwargs):
    print(kwargs)
    print(fct.full_msg)
    time.sleep(3)  # 框架会自动并发绕开这个阻塞，无论函数内部随机耗时多久都能自动调节并发达到每秒运行 5 次 这个 task_fun 函数的目的。


if __name__ == "__main__":
    redis_conn = redis.Redis(db=7)
    for i in range(10):
        task_fun.publish(dict(x=i, y=i * 2, x3=6, x4=8, x5={'k1': i, 'k2': i * 2, 'k3': i * 3}))  # 发布者发布任务
        task_fun.publisher.send_msg(dict(y1=i, y2=i * 2, y3=6, y4=8, y5={'k1': i, 'k2': i * 2, 'k3': i * 3})) # send_msg是发送原始消息

        # 用户和其他部门的java golang员工发送的自由格式任意消息，也能被funboost消费，也即是说无视是否使用funboost来发消息，funboost都能消费。
        # funboost消费兼容性太强了，这一点完爆celery。
        redis_conn.lpush('task_queue_name2c',json.dumps({"m":666,"n":777})) 

    task_fun.consume()
   
    ctrl_c_recv()

