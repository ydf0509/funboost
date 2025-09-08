import time
import asyncio
import copy
from funboost import boost, BrokerEnum, BoosterParams, ConcurrentModeEnum, ctrl_c_recv
from funboost.utils.class_utils import ClsHelper


# 0. 定义一个自定义类，用于演示pickle序列化
class MyObject:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return f"MyObject(name='{self.name}', value={self.value})"


# 1. 定义一个普通的同步函数
# funboost 默认的并发模式是多线程（ConcurrentModeEnum.THREADING），
# 非常适合执行这种包含 time.sleep 的 IO 阻塞型函数。
@boost(BoosterParams(queue_name='sync_task_queue', broker_kind=BrokerEnum.REDIS_ACK_ABLE, concurrent_mode=ConcurrentModeEnum.THREADING, concurrent_num=5))
def task_sync(x: int, y: int):
    """
    这是一个常规的同步函数。
    """
    print(f"开始执行同步任务: {x} + {y}")
    time.sleep(2)  # 模拟一个耗时的 IO 操作
    result = x + y
    print(f"同步任务完成: {x} + {y} = {result}")
    return result

# 2. 定义一个异步协程函数
# 对于 async def 函数，需要明确指定并发模式为 ASYNC (ConcurrentModeEnum.ASYNC)。
# funboost 会使用一个事件循环来并发地运行这些协程任务。
@boost(BoosterParams(queue_name='async_task_queue', broker_kind=BrokerEnum.REDIS_ACK_ABLE, concurrent_mode=ConcurrentModeEnum.ASYNC, concurrent_num=10))
async def task_async(url: str):
    """
    这是一个异步协程函数。
    """
    print(f"开始执行异步任务: 爬取 {url}")
    await asyncio.sleep(3)  # 模拟一个异步的 aiohttp/httpx 网络请求
    print(f"异步任务完成: 爬取 {url} 成功")
    return f"Success: {url}"


# 3. 定义一个包含实例方法的类
class MyClass:
    def __init__(self, multiplier):
        # 这行代码是必须的，用于funboost在消费时能够重新实例化对象
        self.obj_init_params: dict = ClsHelper.get_obj_init_params_for_funboost(copy.copy(locals()))
        self.multiplier = multiplier
        print(f"MyClass 实例已创建，乘数为: {self.multiplier}")

    # 将@boost装饰器直接应用在实例方法上
    @boost(BoosterParams(queue_name='instance_method_queue', broker_kind=BrokerEnum.REDIS_ACK_ABLE, concurrent_num=3))
    def multiply(self, x: int):
        print(f"开始执行实例方法任务: {x} * {self.multiplier}")
        time.sleep(1)
        result = x * self.multiplier
        print(f"实例方法任务完成: {x} * {self.multiplier} = {result}")
        return result


# 4. 定义一个接收自定义对象的函数，这将触发pickle序列化
@boost(BoosterParams(queue_name='pickle_task_queue', broker_kind=BrokerEnum.REDIS_ACK_ABLE, concurrent_num=3))
def task_with_pickle(obj: MyObject):
    """
    这个函数接收一个自定义对象，funboost会自动使用pickle进行序列化。
    """
    print(f"开始执行 pickle 任务: 接收到对象 {obj}")
    time.sleep(1)
    obj.value += 100
    print(f"Pickle 任务完成: 对象变为 {obj}")
    return str(obj)


if __name__ == '__main__':
    # 5. 清空之前的任务（可选，用于确保测试环境干净）
    task_sync.clear()
    task_async.clear()
    task_with_pickle.clear()
    my_instance = MyClass(multiplier=10)  # 创建一个实例
    my_instance.multiply.clear()


    # 6. 启动所有消费者
    # .consume() 是非阻塞的，它会在后台启动消费者
    task_sync.consume()
    task_async.consume()
    my_instance.multiply.consume()
    task_with_pickle.consume()

    print("\n所有消费者均已启动，等待处理任务...")

    # 7. 发布任务到各自的队列
    print("正在发布任务...")
    for i in range(5):
        task_sync.push(i, i * 2)
        print(task_async.push(f"https://example.com/page/{i}").result)
        my_instance.multiply.push(my_instance, i)  # 发布实例方法任务，需要将实例本身作为第一个参数
        task_with_pickle.push(MyObject(name=f'obj_{i}', value=i)) # 发布一个自定义对象
    print("任务发布完成。")

   
    print("按 Ctrl+C 退出程序。")

    # 8. 阻塞主线程，以便后台的消费者可以持续运行
    ctrl_c_recv()