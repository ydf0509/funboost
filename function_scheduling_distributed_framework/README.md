"""
类celery的worker模式，可用于一切需要分布式并发的地方，最好是io类型的。可以分布式调度起一切函数。
rabbitmq生产者和消费者框架。完全实现了celery worker模式的全部功能，使用更简单。支持自动重试指定次数，
消费确认，指定数量的并发线程，和指定频率控制1秒钟只运行几次， 同时对mongodb类型的异常做了特殊处理
最开始写得是使用pika包，非线程安全,后来加入rabbitpy,rabbitpy包推送会丢失部分数据，推荐pika包使用
单下划线代表保护，双下划线代表私有。只要关注公有方法就可以，其余是类内部自调用方法。



3月15日
1）、新增RedisConsumer 是基于redis中间件的消费框架，不支持随意暂停程序或者断点，会丢失一部分正在运行中的任务，推荐使用rabbitmq的方式。
get_consumer是使用工厂模式来生成基于rabbit和reids的消费者，使用不同中间件的消费框架更灵活一点点，只需要修改一个数字。

3月20日
2）、增加支持函数参数过滤的功能，可以随时放心多次推送相同的任务到中间件，会先检查该任务是否需要执行，避免浪费cpu和流量，加快处理速度。
基于函数参数值的过滤，需要设置 do_task_filtering 参数为True才生效，默认为False。
3）、新增支持了函数的参数是多个参数，需要设置is_consuming_function_use_multi_params 为True生效，为了兼容老代码默认为False。
区别是消费函数原来需要
def f(body):   # 函数有且只能有一个参数，是字典的多个键值对来表示参数的值。
    print(body['a'])
    print(body['b'])

现在可以
def f(a,b):
    print(a)
    print(b)

对于推送的部分,都是一样的，都是推送 {"a":1,"b":2}

开启消费都是   get_consumer('queue_test', consuming_function=f).start_consuming_message()

6月3日
1) 增加了RedisPublisher类，和增加get_publisher工厂模式
方法同mqpublisher一样，这是为了增强一致性，以后每个业务的推送和消费，
如果不直接使用RedisPublisher  RedisConsumerer RabbitmqPublisher RabbitMQConsumer这些类，而是使用get_publisher和get_consumer来获取发布和消费对象，
支持修改一个全局变量的broker_kind数字来切换所有平台消费和推送的中间件种类。
2）增加指定不运行的时间的配置。例如可以白天不运行，只在晚上运行。
3）增加了函数超时的配置，当函数运行时间超过n秒后，自动杀死函数，抛出异常。
4) 增加每分钟函数运行次数统计，和按照最近一分钟运行函数次数来预估多久可以运行完成当前队列剩余的任务。
5） 增加一个判断函数，阻塞判断连续多少分钟队列里面是空的。判断任务疑似完成。
6）增加一个终止消费者的标志，设置标志后终止循环调度消息。
7) consumer对象增加内置一个属性，表示相同队列名的publisher实例。

6月29日
1） 增加消息过期时间的配置，消费时候距离发布时候超过一定时间，丢弃任务。
2）增加基于python内置Queue对象的本地队列作为中间件的发布者和消费者，公有方法的用法与redis和mq的完全一致，
方便没有安装mq和redis的环境使用测试除分布式以外的其他主要功能。使用内置queue无法分布式和不支持程序重启任务接续。
好处是可以改一个数字就把代码运行起来在本地测试，不会接受和推送消息到中间件影响别人，别人也影响不了自己，自测很合适。
3）实例化发布者时候，不在初始化方法中链接中间件，延迟到首次真正使用操作中间件的方法。
4)BoundedThreadpoolExecutor替换成了新的CustomThreadpoolExecutor


7月2日
加入了gevent并发模式，设置concurrent_mode为2生效。

7月3日
加入了evenlet并发模式，设置concurrent_mode为3生效。

7月4日
1）增加使用amqpstorm实现的rabbit操作的中间件，设置broker_kind为4生效，支持消费确认
2）增加mongo-queue实现的mongodb为中间件的队列，设置broker_kind为5生效，支持确认消费
3）增加persistqueue sqllite3实现的本地持久化队列，支持多进程和多次启动不在同一个解释器下的本地分布式。比python内置Queue对象增加了持久化和支持不同启动批次的脚本推送 消费。sqllite不需要安装这个中间件就可以更方便使用。设置broker_kind为6生效，支持确认消费。

"""