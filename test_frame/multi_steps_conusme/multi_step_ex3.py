
"""
此代码
1.演示支持多个函数消费队列的无阻塞启动（consume不会阻塞主线程）
2.演示支持在一个消费函数内部向任意队列发布新任务，实现多级任务链
代码结构清晰，扩展性极强
"""
from funboost import boost, BrokerEnum,BoosterParams,ctrl_c_recv,ConcurrentModeEnum
import time

class MyBoosterParams(BoosterParams):  # 自定义的参数类，继承BoosterParams，用于减少每个消费函数装饰器的重复相同入参个数
    broker_kind: str = BrokerEnum.MEMORY_QUEUE
    max_retry_times: int = 3
    concurrent_mode: str = ConcurrentModeEnum.THREADING 

    
@boost(MyBoosterParams(queue_name='s1_queue', qps=1, ))
def step1(a:int,b:int):
    print(f'a={a},b={b}')
    time.sleep(0.7)
    for j in range(10):
        step2.push(c=a+b +j,d=a*b +j,e=a-b +j ) # step1消费函数里面，也可以继续向其他任意队列发布消息。
    return a+b


@boost(MyBoosterParams(queue_name='s2_queue', qps=3, ))
def step2(c:int,d:int,e:int):
    time.sleep(3)
    print(f'c={c},d={d},e={e}')
    return c* d * e


if __name__ == '__main__':
    for i in range(100):
        step1.push(i,i*2) # 向 step1函数的队列发送消息。
    step1.consume() # 调用.consume是非阻塞的，是在单独的子线程中循环拉取消息的。 有的人还担心阻塞而手动使用 threading.Thread(target=step1.consume) 来启动消费，这是完全多此一举的错误写法。
    step2.consume() # 所以可以连续无阻塞丝滑的启动多个函数消费。
    ctrl_c_recv()

