# distributed_framework
```
python分布式函数调度框架。适用场景范围超级广泛。
将函数名和队列名绑定，即可开启自动消费。
只需要一行代码就 将任何函数实现 分布式 、并发、 控频、断点接续运行、定时、指定时间不运行、
消费确认、重试指定次数、重新入队、超时杀死、计算消费次数速度、预估消费时间、
函数运行日志记录、任务过滤、任务过期丢弃等数十种功能。
和celery一样支持线程、gevent、eventlet 并发运行模式，大大简化比使用celery，很强大简单，已在多个生产项目和模块验证。
```



##  具体更详细的用法可以看test_frame文件夹里面的几个示例。
 ```python
import time

from function_scheduling_distributed_framework import patch_frame_config, show_frame_config,get_consumer


# 初次接触使用，可以不安装任何中间件，使用本地持久化队列。正式墙裂推荐安装rabbitmq。
patch_frame_config(MONGO_CONNECT_URL='mongodb://myUserAdminxx:xxxx@xx.90.89.xx:27016/admin',

                   RABBITMQ_USER='silxxxx',
                   RABBITMQ_PASS='Fr3Mxxxxx',
                   RABBITMQ_HOST='1xx.90.89.xx',
                   RABBITMQ_PORT=5672,
                   RABBITMQ_VIRTUAL_HOST='test_host',

                   REDIS_HOST='1xx.90.89.xx',
                   REDIS_PASSWORD='yxxxxxxR',
                   REDIS_PORT=6543,
                   REDIS_DB=7, )

show_frame_config()

# 主要的消费函数，演示做加法，假设需要花10秒钟。
def f2(a, b):
    print(f'消费此消息 {a} + {b} ,结果是  {a + b}')
    time.sleep(10)  # 模拟做某事需要阻塞10秒种，必须用并发绕过此阻塞。


# 把消费的函数名传给consuming_function，就这么简单。
# 通过设置broker_kind，一键切换中间件为mq或redis等7种中间件或包。
# 额外参数支持超过10种控制功能，celery支持的控制方式，都全部支持。
# 这里演示使用本地持久化队列，本机多个脚本之间可以共享任务，无需安装任何中间件，降低初次使用门槛。
consumer = get_consumer('queue_test2', consuming_function=f2, broker_kind=6)  



# 推送需要消费的任务，可以变消费边推送。发布的内容字典需要和函数所能接收的参数一一对应，
# 并且函数参数需要能被json序列化，不要把自定义的类型作为消费函数的参数。
consumer.publisher_of_same_queue.clear()
[consumer.publisher_of_same_queue.publish({'a': i, 'b': 2 * i}) for i in range(100)]


# 开始从中间件循环取出任务，使用指定的函数消费中间件里面的消息。
consumer.start_consuming_message()

 ```
 
### 运行中截图
![Image text](http://chuantu.xyz/t6/702/1565270169x1031866013.png)
### 控频功能证明，由于截图是外网调度rabbitmq的消息有延迟，没有精确到函数每秒运行10次。
![Image text](http://chuantu.xyz/t6/702/1565260798x1031866013.png)