# coding= utf-8



class   BrokerEnum:
    """
    在funboost中万物皆可为消息队列broker,funboost内置了所有 知名的正经经典消息队列作为broker,
    也支持了基于 内存 各种数据库 文件系统 tcp/udp/http这些socket 模拟作为broker.
    funboost也内置支持了各种python三方包和消费框架作为broker,例如 sqlachemy kombu celery rq dramtiq huey nameko 等等

    用户也可以按照文档4.21章节,轻松扩展任何物质概念作为funboost的broker.
    """
    
    # funboost框架能轻松兼容消息队列各种工作模式, 拉模式/推模式/轮询模式，单条获取 批量获取
    """
    funboost 的 consumer的 _shedual_task 非常灵活，用户实现把从消息队列取出的消息通过_submit_task方法
    丢到并发池，他不是强制用户重写实现怎么取一条消息，例如强制你实现一个 _get_one_message的法，
    那就不灵活和限制扩展任意东西作为broker了，而是用户完全自己来写灵活代码。
    所以无论获取消息是 拉模式 还是推模式 还是轮询模式，是单条获取 还是多条批量获取，
    不管你的新中间件和rabbitmq api用法差别有多么巨大，都能轻松扩展任意东西作为funboost的中间件。 
    所以你能看到funboost源码中能轻松实现任物质概念作为funboost的broker。
    """


    EMPTY = 'EMPTY'  # 空的实现，需要搭配 boost入参的 consumer_override_cls 和 publisher_override_cls使用，或者被继承。

    RABBITMQ_AMQPSTORM = 'RABBITMQ_AMQPSTORM'  # 使用 amqpstorm 包操作rabbitmq  作为 分布式消息队列，支持消费确认.强烈推荐这个作为funboost中间件。
    RABBITMQ = RABBITMQ_AMQPSTORM

    # 2025-10 内置新增, 支持rabbitmq 所有路由模式,包括 fanout,direct,topic,headers. 使用概念更复杂
    # 用法见 test_frame/test_broker_rabbitmq/test_rabbitmq_complex_routing 中的demo代码.
    RABBITMQ_COMPLEX_ROUTING = 'RABBITMQ_COMPLEX_ROUTING'

    RABBITMQ_RABBITPY = 'RABBITMQ_RABBITPY'  # 使用 rabbitpy 包操作rabbitmq  作为 分布式消息队列，支持消费确认，不建议使用

    """
    以下是各种redis数据结构和各种方式来实现作为消息队列的,redis简直被作者玩出花来了.
    因为redis本身是缓存数据库,不是消息队列,redis没有实现经典AMQP协议,所以redis是模拟消息队列不是真消息队列.
    例如要实现消费确认,随意重启但消息万无一失,你搞个简单的 redis.blpop 弹出删除消息,那就压根不行.重启就丢失了,但消息可能还没开始运行或者正在运行中.
    
    redis做ack挑战难点不是怎么实现确认消费本身,而是何时应该把关闭或宕机进程的消费者的待确认消费的孤儿消息重回队列.  
    在 Redis 上实现 ACK 的真正难点，根本不在于“确认”这个动作本身，而在于建立一套可靠的、能够准确判断“何时可以安全地及时地进行任务恢复”的分布式故障检测机制。
    所以你以为只要使用 brpoplpush 或者 REDIS_STREAM 就能自动轻易解决ack问题,那就太天真了,因为redis服务端不能像rabbitmq服务端那样天生自带自动重回宕机消费者的消息机制,需要你在redis客户端来维护实现这套机制.
    """
    REDIS = 'REDIS'  # 使用 redis 的 list结构，brpop 作为分布式消息队列。随意重启和关闭会丢失大量消息，不支持消费确认。注重性能不在乎丢失消息可以选这个redis方案。
    REDIS_ACK_ABLE = 'REDIS_ACK_ABLE'  # 基于redis的 list + 临时unack的set队列，采用了 lua脚本操持了取任务和加到pengding为原子性，,基于进程心跳消失判断消息是否为掉线进程的，随意重启和掉线不会丢失任务。
    REIDS_ACK_USING_TIMEOUT = 'reids_ack_using_timeout'  # 基于redis的 list + 临时unack的set队列，使用超时多少秒没确认消费就自动重回队列，请注意 ack_timeout的设置值和函数耗时大小，否则会发生反复重回队列的后果,boost可以设置ack超时，broker_exclusive_config={'ack_timeout': 1800}.缺点是无法区分执行太慢还是真宕机
    REDIS_PRIORITY = 'REDIS_PRIORITY'  # # 基于redis的多 list + 临时unack的set队列，blpop监听多个key，和rabbitmq的x-max-priority属性一样，支持任务优先级。看文档4.29优先级队列说明。
    REDIS_STREAM = 'REDIS_STREAM'  # 基于redis 5.0 版本以后，使用 stream 数据结构作为分布式消息队列，支持消费确认和持久化和分组消费，是redis官方推荐的消息队列形式，比list结构更适合。
    RedisBrpopLpush = 'RedisBrpopLpush'  # 基于redis的list结构但是采用 brpoplpush 双队列形式，和 redis_ack_able的实现差不多，实现上采用了原生命令就不需要lua脚本来实现取出和加入unack了。
    REDIS_PUBSUB = 'REDIS_PUBSUB'  # 基于redis 发布订阅的，发布一个消息多个消费者都能收到同一条消息，但不支持持久化

    MEMORY_QUEUE = 'MEMORY_QUEUE'  # 使用python queue.Queue实现的基于当前python进程的消息队列，不支持跨进程 跨脚本 跨机器共享任务，不支持持久化，适合一次性短期简单任务。
    LOCAL_PYTHON_QUEUE = MEMORY_QUEUE  # 别名，python本地queue就是基于python自带的语言的queue.Queue，消息存在python程序的内存中，不支持重启断点接续。

    RABBITMQ_PIKA = 'RABBITMQ_PIKA'  # 使用pika包操作rabbitmq  作为 分布式消息队列。，不建议使用

    MONGOMQ = 'MONGOMQ'  # 使用mongo的表中的行模拟的 作为分布式消息队列，支持消费确认。

    SQLITE_QUEUE = 'sqlite3'  # 使用基于sqlite3模拟消息队列，支持消费确认和持久化，但不支持跨机器共享任务，可以基于本机单机跨脚本和跨进程共享任务，好处是不需要安装中间件。
    PERSISTQUEUE = SQLITE_QUEUE  # PERSISTQUEUE的别名

    NSQ = 'NSQ'  # 基于nsq作为分布式消息队列，支持消费确认。

    KAFKA = 'KAFKA'  # 基于kafka作为分布式消息队列，如果随意重启会丢失消息，建议使用BrokerEnum.CONFLUENT_KAFKA。

    """基于confluent-kafka包，包的性能比kafka-python提升10倍。同时应对反复随意重启部署消费代码的场景，此消费者实现至少消费一次，第8种BrokerEnum.KAFKA是最多消费一次。"""
    KAFKA_CONFLUENT = 'KAFKA_CONFLUENT'
    CONFLUENT_KAFKA = KAFKA_CONFLUENT

    KAFKA_CONFLUENT_SASlPlAIN = 'KAFKA_CONFLUENT_SASlPlAIN'  # 可以设置账号密码的kafka

    SQLACHEMY = 'SQLACHEMY'  # 基于SQLACHEMY 的连接作为分布式消息队列中间件支持持久化和消费确认。支持mysql oracle sqlserver等5种数据库。

    ROCKETMQ = 'ROCKETMQ'  # 基于 rocketmq 作为分布式消息队列，这个中间件必须在linux下运行，win不支持。

    ZEROMQ = 'ZEROMQ'  # 基于zeromq作为分布式消息队列，不需要安装中间件，可以支持跨机器但不支持持久化。


    """
    kombu 和 celery 都是 funboost中的神级别broker_kind。
    使得funboost以逸待劳，支持kombu的所有现有和未来的消息队列。
    通过直接支持 kombu，funboost 相当于一瞬间就继承了 `kombu` 支持的所有现有和未来的消息队列能力。无论 kombu 社区未来增加了对哪种新的云消息服务（如 Google
    Pub/Sub、Azure Service Bus）或小众 MQ 的支持，funboost 无需修改自身代码，就能自动获得这种能力。这
    是一种“以逸待劳”的策略，极大地扩展了 funboost 的适用范围。

    kombu 包可以作为funboost的broker，这个包也是celery的中间件依赖包，这个包可以操作10种中间件(例如rabbitmq redis)，但没包括分布式函数调度框架的kafka nsq zeromq 等。
    同时 kombu 包的性能非常差，可以用原生redis的lpush和kombu的publish测试发布，使用brpop 和 kombu 的 drain_events测试消费，对比差距相差了5到10倍。
    由于性能差，除非是分布式函数调度框架没实现的中间件才选kombu方式(例如kombu支持亚马逊队列  qpid pyro 队列)，否则强烈建议使用此框架的操作中间件方式而不是使用kombu。
    """
    KOMBU = 'KOMBU'

    """ 基于emq作为中间件的。这个和上面的中间件有很大不同，服务端不存储消息。所以不能先发布几十万个消息，然后再启动消费。mqtt优点是web前后端能交互，
    前端不能操作redis rabbitmq kafka，但很方便操作mqtt。这种使用场景是高实时的互联网接口。
    """
    MQTT = 'MQTT'

    HTTPSQS = 'HTTPSQS'  # httpsqs中间件实现的，基于http协议操作，dcoker安装此中间件简单。

    PULSAR = 'PULSAR'  # 最有潜力的下一代分布式消息系统。5年后会同时取代rabbitmq和kafka。

    UDP = 'UDP'  # 基于socket udp 实现的，需要先启动消费端再启动发布，支持分布式但不支持持久化，好处是不需要安装消息队列中间件软件。

    TCP = 'TCP'  # 基于socket tcp 实现的，需要先启动消费端再启动发布，支持分布式但不支持持久化，好处是不需要安装消息队列中间件软件。

    HTTP = 'HTTP'  # 基于http实现的，发布使用的urllib3，消费服务端使用的aiohttp.server实现的，支持分布式但不支持持久化，好处是不需要安装消息队列中间件软件。

    GRPC = 'GRPC' # 使用知名grpc作为broker,可以使用 sync_call 方法同步获取grpc的结果, 简单程度暴击用户手写原生的 grpc客户端 服务端

    NATS = 'NATS'  # 高性能中间件nats,中间件服务端性能很好,。

    TXT_FILE = 'TXT_FILE'  # 磁盘txt文件作为消息队列，支持单机持久化，不支持多机分布式。不建议这个，用sqlite。

    PEEWEE = 'PEEWEE'  # peewee包操作mysql，使用表模拟消息队列

    CELERY = 'CELERY'  # funboost支持celery框架来发布和消费任务，由celery框架来调度执行任务，但是写法简单远远暴击用户亲自使用celery的麻烦程度，
    # 用户永无无需关心和操作Celery对象实例,无需关心celery的task_routes和includes配置,funboost来自动化设置这些celery配置。
    # funboost将Celery本身纳入了自己的Broker体系。能“吞下”另一个大型框架，简直太妙了。本身就证明了funboost架构的包容性和精妙性和复杂性。

    DRAMATIQ = 'DRAMATIQ'  # funboost使用 dramatiq 框架作为消息队列，dramatiq类似celery也是任务队列框架。用户使用funboost api来操作dramatiq核心调度。

    HUEY = 'HUEY'  # huey任务队列框架作为funboost调度核心

    RQ = 'RQ'  # rq任务队列框架作为funboost调度核心

    NAMEKO = 'NAMEKO'  # funboost支持python微服务框架nameko，用户无需掌握nameko api语法，就玩转python nameko微服务

    
    """
    MYSQL_CDC 是 funboost 中 神奇 的 与众不同的 broker 中间件
    mysql binlog cdc 自动作为消息,用户无需手动发布消息,只需要写处理binlog内容的逻辑, 
    一行代码就能轻量级实现 mysql2mysql mysql2kafka mysql2rabbitmq 等等.
    这个是与其他中间件不同,不需要手工发布消息, 任何对数据库的 insert update delete 会自动作为 funboost 的消息.
    几乎是轻量级平替 canal  flinkcdc 的作用.
    
    以此类推, 日志文件也能扩展作为broker,只要另外一个程序写入了文件日志,就能触发funboost消费,
    然后自己在函数逻辑把消息发到kafka,(虽然是已经有大名鼎鼎elk,这只是举个场景例子,说明funboost broker的灵活性)

    日志文件、文件系统变更（inotify）、甚至是硬件传感器的信号，按照4.21章节文档，都可以被封装成一个 funboost 的 Broker。

    充分说明 funboost 有能力化身为 通用的、事件驱动的函数调度平台,而非仅仅是celery这种传统的消息驱动.
    """
    """
    funboost 有能力消费canal发到kafka的binlog消息,也能不依赖canal,自己捕获cdc数据
    """
    MYSQL_CDC = 'MYSQL_CDC'



class ConcurrentModeEnum:
    THREADING = 'threading'  # 线程方式运行，兼容支持 async def 的异步函数。
    GEVENT = 'gevent'
    EVENTLET = 'eventlet'
    ASYNC = 'async'  # asyncio并发，适用于async def定义的函数。
    SINGLE_THREAD = 'single_thread'  # 如果你不想并发，不想预先从消息队列中间件拉取消息到python程序的内存queue队列缓冲中，那么就适合使用此并发模式。
    SOLO = SINGLE_THREAD


# is_fsdf_remote_run = 0

class FunctionKind:
    CLASS_METHOD = 'CLASS_METHOD'
    INSTANCE_METHOD = 'INSTANCE_METHOD'
    STATIC_METHOD = 'STATIC_METHOD'
    COMMON_FUNCTION = 'COMMON_FUNCTION'


class ConstStrForClassMethod:
    FIRST_PARAM_NAME = 'first_param_name'
    CLS_NAME = 'cls_name'
    OBJ_INIT_PARAMS = 'obj_init_params'
    CLS_MODULE = 'cls_module'
    CLS_FILE = 'cls_file'


class RedisKeys:

    REDIS_KEY_PAUSE_FLAG  = 'funboost_pause_flag' 
    REDIS_KEY_STOP_FLAG = 'funboost_stop_flag'
    QUEUE__MSG_COUNT_MAP = 'funboost_queue__msg_count_map'
    FUNBOOST_QUEUE__CONSUMER_PARAMS= 'funboost_queue__consumer_parmas'
    FUNBOOST_QUEUE__RUN_COUNT_MAP = 'funboost_queue__run_count_map'
    FUNBOOST_QUEUE__RUN_FAIL_COUNT_MAP = 'funboost_queue__run_fail_count_map'
    FUNBOOST_ALL_QUEUE_NAMES = 'funboost_all_queue_names'
    FUNBOOST_ALL_IPS = 'funboost_all_ips'
    FUNBOOST_ALL_PROJECT_NAMES = 'funboost_all_project_names'
    FUNBOOST_LAST_GET_QUEUES_PARAMS_AND_ACTIVE_CONSUMERS_AND_REPORT__UUID_TS = 'funboost_last_get_queues_params_and_active_consumers_and_report__uuid_ts'

    FUNBOOST_HEARTBEAT_QUEUE__DICT_PREFIX = 'funboost_hearbeat_queue__dict:'
    FUNBOOST_HEARTBEAT_SERVER__DICT_PREFIX = 'funboost_hearbeat_server__dict:'


    @staticmethod
    def gen_funboost_apscheduler_redis_lock_key_by_queue_name(queue_name):
        return f'funboost.BackgroundSchedulerProcessJobsWithinRedisLock:{queue_name}'

    @staticmethod
    def gen_funboost_hearbeat_queue__dict_key_by_queue_name(queue_name):
        return f'{RedisKeys.FUNBOOST_HEARTBEAT_QUEUE__DICT_PREFIX}{queue_name}'

    @staticmethod
    def gen_funboost_hearbeat_server__dict_key_by_ip(ip):
        return f'{RedisKeys.FUNBOOST_HEARTBEAT_SERVER__DICT_PREFIX}{ip}'
    
    @staticmethod
    def gen_funboost_queue_time_series_data_key_by_queue_name(queue_name):
        return f'funboost_queue_time_series_data:{queue_name}'
    
    @staticmethod
    def gen_funboost_redis_apscheduler_jobs_key_by_queue_name(queue_name):
        jobs_key=f'funboost.apscheduler.jobs:{queue_name}'
        return jobs_key
    
    @staticmethod
    def gen_funboost_redis_apscheduler_run_times_key_by_queue_name(queue_name):
        run_times_key=f'funboost.apscheduler.run_times:{queue_name}'
        return run_times_key

    @staticmethod
    def gen_funboost_project_name_key(project_name):
        prject_name_key = f'funboost.project_name:{project_name}'
        return prject_name_key

class ConsumingFuncInputParamsCheckerField:
    is_manual_func_input_params = 'is_manual_func_input_params'
    all_arg_name_list = 'all_arg_name_list'
    must_arg_name_list = 'must_arg_name_list'
    optional_arg_name_list = 'optional_arg_name_list'
    func_name = 'func_name' 
    func_position = 'func_position'
    

class MongoDbName:
    TASK_STATUS_DB = 'funboost_task_status'
    MONGOMQ_DB ='funboost_mongomq'
