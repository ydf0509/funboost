# coding= utf-8
class BrokerEnum:
    RABBITMQ_AMQPSTORM = 0  # 使用 amqpstorm 包操作rabbitmq  作为 分布式消息队列，支持消费确认.推荐这个。

    RABBITMQ_RABBITPY = 1  # 使用 rabbitpy 包操作rabbitmq  作为 分布式消息队列，支持消费确认。

    REDIS = 2  # 使用 redis 的 list结构，brpop 作为分布式消息队列。随意重启和关闭会丢失大量消息，不支持消费确认。注重性能不在乎丢失消息可以选这个redis方案。

    LOCAL_PYTHON_QUEUE = 3  # 使用python queue.Queue实现的基于当前python进程的消息队列，不支持跨进程 跨脚本 跨机器共享任务，不支持持久化，适合一次性短期简单任务。
    MEMORY_QUEUE = LOCAL_PYTHON_QUEUE  # 别名，python本地queue就是基于python自带的语言的queue.Queue，消息存在python程序的内存中，不支持重启断点接续。

    RABBITMQ_PIKA = 4  # 使用pika包操作rabbitmq  作为 分布式消息队列。

    MONGOMQ = 5  # 使用mongo的表中的行模拟的 作为分布式消息队列，支持消费确认。

    PERSISTQUEUE = 6  # 使用基于sqlute3模拟消息队列，支持消费确认和持久化，但不支持跨机器共享任务，可以基于本机单机跨脚本和跨进程共享任务，好处是不需要安装中间件。
    SQLITE_QUEUE = PERSISTQUEUE  # PERSISTQUEUE的别名

    NSQ = 7  # 基于nsq作为分布式消息队列，支持消费确认。

    KAFKA = 8  # 基于kafka作为分布式消息队列，如果随意重启会丢失消息，建议使用BrokerEnum.CONFLUENT_KAFKA。

    """基于confluent-kafka包，包的性能比kafka-python提升10倍。同时应对反复随意重启部署消费代码的场景，此消费者实现至少消费一次，第8种BrokerEnum.KAFKA是最多消费一次。"""
    CONFLUENT_KAFKA = 16
    KAFKA_CONFLUENT = CONFLUENT_KAFKA

    REDIS_ACK_ABLE = 9  # 基于redis的 list + 临时unack的set队列，采用了 lua脚本操持了取任务和加到pengding为原子性，随意重启和掉线不会丢失任务。
    # 集群里面的所有电脑或服务器时间一定要设置成自动获取，不然会发生消费重复问题，单台没事。

    SQLACHEMY = 10  # 基于SQLACHEMY 的连接作为分布式消息队列中间件支持持久化和消费确认。支持mysql oracle sqlserver等5种数据库。

    ROCKETMQ = 11  # 基于 rocketmq 作为分布式消息队列，这个中间件必须在linux下运行，win不支持。

    REDIS_STREAM = 12  # 基于redis 5.0 版本以后，使用 stream 数据结构作为分布式消息队列，支持消费确认和持久化和分组消费，是redis官方推荐的消息队列形式，比list结构更适合。

    ZEROMQ = 13  # 基于zeromq作为分布式消息队列，不需要安装中间件，可以支持跨机器但不支持持久化。

    RedisBrpopLpush = 14  # 基于redis的list结构但是采用brpoplpush 双队列形式，和 redis_ack_able的实现差不多，实现上采用了原生命令就不需要lua脚本来实现取出和加入unack了。

    """
    操作 kombu 包，这个包也是celery的中间件依赖包，这个包可以操作10种中间件(例如rabbitmq redis)，但没包括分布式函数调度框架的kafka nsq zeromq 等。
    同时 kombu 包的性能非常差，可以用原生redis的lpush和kombu的publish测试发布，使用brpop 和 kombu 的 drain_events测试消费，对比差距相差了5到10倍。
    由于性能差，除非是分布式函数调度框架没实现的中间件才选kombu方式(例如kombu支持亚马逊队列  qpid pyro 队列)，否则强烈建议使用此框架的操作中间件方式而不是使用kombu。
    """
    KOMBU = 15

    """ 基于emq作为中间件的。这个和上面的中间件有很大不同，服务端不存储消息。所以不能先发布几十万个消息，然后再启动消费。mqtt优点是web前后端能交互，
    前端不能操作redis rabbitmq kafka，但很方便操作mqtt。这种使用场景是高实时的互联网接口。
    """
    MQTT = 17

    HTTPSQS = 18  # httpsqs中间件实现的，基于http协议操作，dcoker安装此中间件简单。

    UDP = 21  # 基于socket udp 实现的，需要先启动消费端再启动发布，支持分布式但不支持持久化，好处是不需要安装消息队列中间件软件。

    TCP = 22  # 基于socket tcp 实现的，需要先启动消费端再启动发布，支持分布式但不支持持久化，好处是不需要安装消息队列中间件软件。

    HTTP = 23  # 基于http实现的，发布使用的urllib3，消费服务端使用的aiohttp.server实现的，支持分布式但不支持持久化，好处是不需要安装消息队列中间件软件。

    NATS = 24  # 高性能中间件nats,中间件服务端性能很好,。

    TXT_FILE = 25  # 磁盘txt文件作为消息队列，支持单机持久化，不支持多机分布式。不建议这个，用sqlite。

    PEEWEE = 26  # peewee包操作mysql，使用表模拟消息队列

    PULSAR = 20  # 最有潜力的下一代分布式消息系统。5年后会同时取代rabbitmq和kafka。目前python客户端只支持linux，win不行




class ConcurrentModeEnum:
    THREADING = 1
    GEVENT = 2
    EVENTLET = 3
    ASYNC = 4  # asyncio并发，适用于async def定义的函数。
    SINGLE_THREAD = 5

# is_fsdf_remote_run = 0
