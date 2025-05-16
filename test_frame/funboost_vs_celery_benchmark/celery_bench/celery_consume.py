from celery import Celery
import datetime
# 创建Celery实例，设置broker和backend
app = Celery('namexx', 
             broker='redis://localhost:6379/0',
)

# 定义一个简单的打印任务
@app.task(name='print_number',queue='test_queue_celery02')
def print_number(i):
    if  i % 1000 == 0:
        print(f"{datetime.datetime.now()} 当前数字是: {i}")
    return i  # 返回结果方便查看任务执行状态

# 如果需要在主程序中调用这个任务，可以这样使用：
# 同步调用: print_number.delay(42)
# 异步获取结果: result = print_number.delay(42); print(result.get())



if __name__ == '__main__':
    # 直接在Python中启动worker，不使用命令行
    # 使用--pool=solo参数确保使用单线程模式
    app.worker_main(['worker', '--loglevel=info', '--pool=solo','--queues=test_queue_celery02'])


'''
在win11 + python3.9 + celery 5 + redis 中间件 + amd r7 5800h cpu 环境下测试 + 选择单线程并发模式

celery消费性能测试结果如下：

celery平均每隔3.6秒消费1000条消息，每秒能消费300条消息


'''