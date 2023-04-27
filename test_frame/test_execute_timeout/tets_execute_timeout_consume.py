import random
import time

from funboost import boost

@boost('test_timeout',concurrent_num=5,function_timeout=20,max_retry_times=4)
def add(x,y):
    t_sleep = random.randint(10, 30)
    print(f'计算 {x} + {y} 中。。。。,需要耗费 {t_sleep} 秒时间')
    time.sleep(t_sleep)
    print(f'执行 {x} + {y} 的结果是 {x+y}  ')
    return x+y


if __name__ == '__main__':
    for i in range(100):
        add.push(i,i*2)
    add.consume()


