"""
演示使用 BoostersManager.consume_group($booster_group) 启动消费组

BoostersManager.consume_group(booster_group=GROUP1_NAME)
相当于是内部执行了 f1.consume() f2.consume() 这种分多次启动消费函数,

因为f1和f2的booster_group都是GROUP1_NAME,所以会被启动消费组
"""

import time
from funboost import boost, BoosterParams, BoostersManager, ConcurrentModeEnum
from funboost.utils.ctrl_c_end import ctrl_c_recv


GROUP1_NAME = "my_group1"

# 自定义的参数类，继承BoosterParams，用于减少每个消费函数装饰器的重复相同入参个数,
# 不用相关函数都重复写 booster_group 入参.
class MyGroup1BoosterParams(BoosterParams):
    concurrent_mode: str = ConcurrentModeEnum.SINGLE_THREAD
    booster_group: str = GROUP1_NAME  # 指定消费分组名字


@boost(
    MyGroup1BoosterParams(
         # 使用了自定义类 MyGroup1BoosterParams ,所以 f1的booster_group 会自动指定为 GROUP1_NAME
        queue_name="queue_test_consume_gq1",
    )
)
def f1(x):
    time.sleep(2)
    print(f"f1 {x}")


@boost(
    MyGroup1BoosterParams( 
        # 使用了自定义类 MyGroup1BoosterParams ,所以 f2的booster_group 会自动指定为 GROUP1_NAME
        queue_name="queue_test_consume_gq2",
    )
)
def f2(x):
    time.sleep(2)
    print(f"f2 {x}")


@boost(
    BoosterParams(
        # 没有使用自定义类 MyGroup1BoosterParams 而是直接传入 BoosterParams,所以 f3 的booster_group 是 None
        queue_name="queue_test_consume_gq3",
        concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
    )
)
def f3(x):
    time.sleep(2)
    print(f"f3 {x}")


if __name__ == "__main__":
    for i in range(10):
        f1.push(i)
        f2.push(i)
        f3.push(i)

    # f1.consume() # 分多次启动消费函数,如果嫌麻烦觉得需要一个一个启动有关函数,可以 BoostersManager.consume_group 一次启动一个分组的所有函数的消费
    # f2.consume()

    BoostersManager.consume_group(
        GROUP1_NAME
    )  # 当前进程内启动消费组 GROUP1_NAME , 内部相当于是执行了 f1.consume() f2.consume() 
    # BoostersManager.multi_process_consume_group(GROUP1_NAME,2) # 多进程启动消费组
    ctrl_c_recv()
