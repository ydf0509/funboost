from funboost import boost
from funboost.concurrent_pool.custom_threadpool_executor import ThreadPoolExecutorShrinkAble
from funboost.concurrent_pool.custom_gevent_pool_executor import GeventPoolExecutor

"""
这个是演示多个不同的函数消费者，使用同一个全局的并发池。
如果一次性启动的函数过多，使用这种方式避免每个消费者创建各自的并发池，减少线程/协程资源浪费。
"""

# 总共那个有5种并发池，用户随便选。
pool = ThreadPoolExecutorShrinkAble(300)  # 指定多个消费者使用同一个线程池，


# pool = GeventPoolExecutor(200)

@boost('test_f1_queue', specify_concurrent_pool=pool, qps=3)
def f1(x):
    print(f'x : {x}')


@boost('test_f2_queue', specify_concurrent_pool=pool, qps=2)
def f2(y):
    print(f'y : {y}')


@boost('test_f3_queue', specify_concurrent_pool=pool)
def f3(m, n):
    print(f'm : {m} , n : {n}')


if __name__ == '__main__':
    for i in range(1000):
        f1.push(i)
        f2.push(i)
        f3.push(i, 1 * 2)
    f1.consume()
    f2.consume()
    f3.consume()
