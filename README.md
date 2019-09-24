# 1.distributed_framework
```
1.0.1 
python万能分布式函数调度框架。适用场景范围超级广泛。
可以一行代码分布式并发调度起一切任何老代码的旧函数和新项目的新函数，并提供数十种函数控制功能。

关于稳定性和性能，一句话概括就是直面百万c端用户（包括app和小程序），
已经连续超过两个季度稳定高效运行无事故。

1.0.2
支持python内置Queue对象作为当前解释器下的消息队列。
支持sqlite3作为本机持久化消息队列。
支持pika包实现的使用rabbitmq作为分布式消息队列。
支持rabbitpy包实现的使用rabbitmq作为分布式消息队列。
支持amqpstorm包实现的使用rabbitmq作为分布式消息队列。
支持redis中间件作为分布式消息队列。（不支持消费确认，例如把消息取出来了，但函数还在运行中没有运行完成，
突然关闭程序或断网断电，会造成部分任务丢失【设置的并发数量越大，丢失数量越惨】，所以推荐mq）
支持mongodb中间件作为分布式消息队列。
支持nsq中间件作为分布式消息队列。
支持kafka中间件作为分布式消息队列。
新增支持redis为中间件，但支持消费确认的功能，不会由于随意关闭和断电每次导致丢失几百个任务。

切换任意中间件，代码都不需要做任何变化，不需要关注如何使用中间件的细节。

1.0.3    
源码实现思路基本90%遵守了oop的6个设计原则，很容易扩展中间件。
1、单一职责原则——SRP
2、开闭原则——OCP
3、里式替换原则——LSP
4、依赖倒置原则——DIP
5、接口隔离原则——ISP
6、迪米特原则——LOD
最主要是大量使用了模板模式、工厂模式、策略模式、鸭子类。
可以仿照源码中实现中间件的例子，只需要继承发布者、消费者基类后实现几个抽象方法即可添加新的中间件。


1.0.4
将函数名和队列名绑定，即可开启自动消费。

只需要一行代码就 将任何老物件的旧函数和新项目的新函数实现 分布式 、并发、 控频、断点接续运行、定时、指定时间不运行、
消费确认、重试指定次数、重新入队、超时杀死、计算消费次数速度、预估消费时间、
函数运行日志记录、任务过滤、任务过期丢弃等数十种功能。

和celery一样支持线程、gevent、eventlet 并发运行模式，大大简化比使用celery，很强大简单，已在多个生产项目和模块验证。
确保任何并发模式在linux和windows，一次编写处处运行。不会像celery在windwos上某些功能失效。

没有严格的目录结构，代码可以在各个文件夹层级到处移动，脚本名字可以随便改。不使用令人讨厌的cmd命令行启动。
没有大量使用元编程，使代码性能提高，减少代码拼错概率和降低调用难度。
并且所有重要公有方法和函数设计都不使用*args，**kwargs方式，全部都能使ide智能提示补全参数，一切为了ide智能补全。

1.0.5
框架附带一个超强漂亮可以跳转的日志，可以独立使用。实现了彩色控制台日志（根据日志严重级别，显示不同颜色，
每一行日志都可以鼠标点击自动精确跳转到日志发生的代码地方）、
多进程安全切片的文件日志、日志发邮件、日志发钉钉、日志发elasticsearch、日志发kafka、日志发mongo，
可以按需使用其中的n种日志handler功能，因为是使用的观察者模式。
from function_scheduling_distributed_framework import LogManager就可以使用。
```

# 手机版git上点击下方 view all of README.md


# 1.1  pip安装方式
pip install function_scheduling_distributed_framework --upgrade -i https://pypi.org/simple 


# 2.具体更详细的用法可以看test_frame文件夹里面的几个示例。
# 以下为简单例子。
 ```python
import time

from function_scheduling_distributed_framework import patch_frame_config, show_frame_config,get_consumer


# 初次接触使用，可以不安装任何中间件，使用本地持久化队列。正式墙裂推荐安装rabbitmq。
# 使用打猴子补丁的方式修改框架配置。这里为了演示，列举了所有中间件的参数，
# 实际是只需要对使用到的中间件的配置进行赋值即可。
patch_frame_config(MONGO_CONNECT_URL='mongodb://myUserAdminxx:xxxx@xx.90.89.xx:27016/admin',

                       RABBITMQ_USER='silxxxx',
                       RABBITMQ_PASS='Fr3Mxxxxx',
                       RABBITMQ_HOST='1xx.90.89.xx',
                       RABBITMQ_PORT=5672,
                       RABBITMQ_VIRTUAL_HOST='test_host',

                       REDIS_HOST='1xx.90.89.xx',
                       REDIS_PASSWORD='yxxxxxxR',
                       REDIS_PORT=6543,
                       REDIS_DB=7,

                       NSQD_TCP_ADDRESSES=['xx.112.34.56:4150'],
                       NSQD_HTTP_CLIENT_HOST='12.34.56.78',
                       NSQD_HTTP_CLIENT_PORT=4151,

                       KAFKA_BOOTSTRAP_SERVERS=['12.34.56.78:9092'],
                       )

show_frame_config()

# 主要的消费函数，演示做加法，假设需要花10秒钟。
def f2(a, b):
    print(f'消费此消息 {a} + {b} 中。。。。。')
    time.sleep(10)  # 模拟做某事需要阻塞10秒种，必须用并发绕过此阻塞。
    print(f'计算 {a} + {b} 得到的结果是  {a + b}')


# 把消费的函数名传给consuming_function，就这么简单。
# 通过设置broker_kind，一键切换中间件为mq或redis等7种中间件或包。
# 额外参数支持超过10种控制功能，celery支持的控制方式，都全部支持。
# 这里演示使用本地持久化队列，本机多个脚本之间可以相互通信共享任务，无需安装任何中间件，降低初次使用门槛。
# 框架使用很简单，全部源码的函数和类都不需要深入了解，只需要看懂get_consumer这一个函数的参数就可以就可以。
"""
    使用工厂模式再包一层，通过设置数字来生成基于不同中间件或包的consumer。
    :param queue_name: 队列名字。
    :param consuming_function: 处理消息的函数。  指定队列名字和指定消费函数这两个参数是必传，必须指定，
           这2个是这个消费框架的本质核心参数，其他参数都是可选的。
    :param function_timeout : 超时秒数，函数运行超过这个时间，则自动杀死函数。为0是不限制。
    :param threads_num:并发数量，协程或线程。由concurrent_mode决定并发种类。
    :param specify_threadpool:使用指定的线程池（协程池），可以多个消费者共使用一个线程池，不为None时候。threads_num失效
    :param concurrent_mode:并发模式，1线程 2gevent 3eventlet
    :param max_retry_times: 最大自动重试次数，当函数发生错误，立即自动重试运行n次，对一些特殊不稳定情况会有效果。
    可以在函数中主动抛出重试的异常ExceptionForRetry，框架也会立即自动重试。 主动抛出ExceptionForRequeue异常，则当前消息会重返中间件。
    :param log_level:框架的日志级别。
    :param is_print_detail_exception:是否打印详细的堆栈错误。为0则打印简略的错误占用控制台屏幕行数少。
    :param msg_schedule_time_intercal:消息调度的时间间隔，用于控频的关键。
    :param msg_expire_senconds:消息过期时间，为0永不过期，为10则代表，10秒之前发布的任务如果现在才轮到消费则丢弃任务。
    :param logger_prefix: 日志前缀，可使不同的消费者生成不同的日志
    :param create_logger_file : 是否创建文件日志
    :param do_task_filtering :是否执行基于函数参数的任务过滤
    :param is_consuming_function_use_multi_params  函数的参数是否是传统的多参数，不为单个body字典表示多个参数。
    :param is_do_not_run_by_specify_time_effect :是否使不运行的时间段生效
    :param do_not_run_by_specify_time   :不运行的时间段
    :param schedule_tasks_on_main_thread :直接在主线程调度任务，意味着不能直接在当前主线程同时开启两个消费者。
    :param function_result_status_persistance_conf   :配置。是否保存函数的入参，运行结果和运行状态到mongodb。这一步用于后续的参数追溯，
           任务统计和web展示，需要安装mongo。
    :param broker_kind:中间件种类,。 0 使用pika链接rabbitmqmq，1使用rabbitpy包实现的操作rabbitmnq，2使用redis，3使用python内置Queue,
           4使用amqpstorm包实现的操作rabbitmq，5使用mongo，6使用sqlite。7使用nsq，8使用kafka，9也是使用redis但支持消费确认。
    :return AbstractConsumer
"""
consumer = get_consumer('queue_test2', consuming_function=f2, broker_kind=6)  


# 推送需要消费的任务，可以变消费边推送。发布的内容字典需要和函数所能接收的参数一一对应，
# 并且函数参数需要能被json序列化，不要把自定义的类型作为消费函数的参数。
consumer.publisher_of_same_queue.clear()
[consumer.publisher_of_same_queue.publish({'a': i, 'b': 2 * i}) for i in range(100)]


# 开始从中间件循环取出任务，使用指定的函数消费中间件里面的消息。
consumer.start_consuming_message()

 ```

### 2.2 windows运行中截图
 
 
 
### 3.1.1 windows运行中截图
![Image text](https://i.niupic.com/images/2019/08/09/_477.png)

### 3.1.2 linux运行中截图,使用gevent模式，减法消费控频更厉害，所以执行次数更少。
![Image text](https://i.niupic.com/images/2019/09/16/_222.png)

### 3.2控频功能证明，由于截图是外网调度rabbitmq的消息有延迟，没有精确到函数每秒运行10次。

![Image text](https://i.niupic.com/images/2019/08/09/_462.png)

### 3.1.3 函数执行结果及状态搜索查看
(需要设置函数状态持久化为True才支持此项功能，默认不开启函数状态结果持久化，
使用的是自动批量聚合插入mongo的方式，需要安装mongodb)。

![Image text](http://i1.fuimg.com/699839/bebd8cddb9ac1260.png)

实测在进行阻塞式任务时候，性能略超过celery。

1)高并发
![Image text](https://i.niupic.com/images/2019/09/20/_331.png)

2)函数结果和运行次数和错误异常查看。使用的测试函数如下。
```
def add(a, b):
    logger.info(f'消费此消息 {a} + {b} 中。。。。。')
    time.sleep(random.randint(3, 5))  # 模拟做某事需要阻塞10秒种，必须用并发绕过此阻塞。
    if random.randint(4, 6) == 5:
        raise RandomError('演示随机出错')
    logger.info(f'计算 {a} + {b} 得到的结果是  {a + b}')
    return a + b
```
![Image text](http://i2.tiimg.com/699839/e9fdcb247fee663d.png)

3)任务消费统计曲线。
![Image text](http://i2.tiimg.com/699839/62e857fb050fc67d.png)

### 3.1.4 我开发时候的状态和使用的是pycharm工具和测试。
在修改为每行最大240个字符后，其余的任何警告级别都保持默认的情况下，
所有文件任意一行在pycahrm的code编辑区域的滚动条做到了0个黄色，和使用alt + shift + i检查，符合极致的pep8规则。
![Image text](http://i2.tiimg.com/699839/d0df7dda607bac79.png)

## 4.celery和这个框架比，存储的内容差异
### 4.1celery的
 ```
 {
  "body": "W1szLCA2XSwge30sIHsiY2FsbGJhY2tzIjogbnVsbCwgImVycmJhY2tzIjogbnVsbCwgImNoYWluIjogbnVsbCwgImNob3JkIjogbnVsbH1d",
   "content-encoding":  "utf-8",
   "content-type":  "application/json",
   "headers":  {
    "lang":  "py",
     "task":  "test_task\u554a",
     "id":  "39198371-8e6a-4994-9f6b-0335fe2e9b92",
     "shadow":  null,
     "eta":  null,
     "expires":  null,
     "group":  null,
     "retries":  0,
     "timelimit":  [
      null,
       null
    ],
     "root_id":  "39198371-8e6a-4994-9f6b-0335fe2e9b92",
     "parent_id":  null,
     "argsrepr":  "(3, 6)",
     "kwargsrepr":  "{}",
     "origin":  "gen22848@FQ9H7TVDZLJ4RBT"
  },
   "properties":  {
    "correlation_id":  "39198371-8e6a-4994-9f6b-0335fe2e9b92",
     "reply_to":  "3ef38b98-1417-3f3d-995b-89e8e15849fa",
     "delivery_mode":  2,
     "delivery_info":  {
      "exchange":  "",
       "routing_key":  "test_a"
    },
     "priority":  0,
     "body_encoding":  "base64",
     "delivery_tag":  "59e39055-2086-4be8-a801-993061fee443"
  }
}
  ```

### 4.2 此框架的消息很短，就是一个字典，内容的键值对和函数入参一一对应。
额外控制参数如重试、超时kill，由代码决定，
不需要存到中间件里面去。例如函数运行超时大小在本地代码修改后，立即生效。

不由中间件里面的配置来决定。
 ```   
{"a":3,"b":6}
  ```
  



# 5.常见问题回答
#### 5.1 你干嘛要写这个框架？和celery 、rq有什么区别？是不是完全重复造轮子为了装x？

  ```
 答：与rq相比，rq只是基于redis一种中间件键，并且连最基本的并发方式和并发数量都没法指定
，更不用说包括控频 等一系列辅助控制功能，功能比celery差太远了，也和此框架不能比较。

这个框架的最开始实现绝对没有受到celery框架的半点启发。
这是从无数个无限重复复制粘贴扣字的使用redis队列的py文件中提取出来的框架。


原来有无数个这样的脚本。以下为伪代码演示，实际代码大概就是这个意思。

while 1：
    msg = redis_client.lpop('queue_namex')
    funcx(msg)

原来有很多个这样的一些列脚本，无限次地把操作redis写到业务流了。
排除无限重复复制粘贴不说，这样除了redis分布式以外，缺少了并发、
 控频、断点接续运行、定时、指定时间不运行、
消费确认、重试指定次数、重新入队、超时杀死、计算消费次数速度、预估消费时间、
函数运行日志记录、任务过滤、任务过期丢弃等数十种功能。

所以这个没有借鉴celery，只是使用oop转化公式提取了可复用流程的类，然后慢慢增加各种辅助控制功能和中间件。
这个和celery一样都属于万能分布式函数调度框架，函数控制功能比rq丰富。比celery的优点见以下解答。

  ```

#### 5.2 为什么包的名字这么长，为什么不学celery把包名取成  花菜 茄子什么的？
  ```
  答： 为了直接表达框架的意思。
   ```
#### 5.3 支持哪些消息队列中间件。
   ```
   答： 支持python内置Queue对象作为当前解释器下的消息队列。
        支持sqlite3作为本机持久化消息队列。
        支持pika包实现的使用rabbitmq作为分布式消息队列。
        支持rabbitpy包实现的使用rabbitmq作为分布式消息队列。
        支持amqpstorm包实现的使用rabbitmq作为分布式消息队列。
        支持redis中间件作为分布式消息队列。（不支持消费确认，例如把消息取出来了，但函数还在运行中没有运行完成，
        突然关闭程序或断网断电，会造成部分任务丢失【设置的并发数量越大，丢失数量越惨】，所以推荐mq）
        支持mongodb中间件作为分布式消息队列。
```
 
 #### 5.4 各种中间件的优劣？
   ```
   答： python内置Queue对象作为当前解释器下的消息队列，
       优势：不需要安装任何中间件，消息存储在解释器的变量内存中，调度没有io，传输速度损耗极小，
             和直接一个函数直接调用另一个函数差不多快。
       劣势：只支持同一个解释器下的任务队列共享，不支持单独启动的两个脚本共享消息任务。  
             没有持久化，解释器退出消息就消失，代码不能中断。   没有分布式。
   
       persistqueue sqlite3作为本机持久化消息队列，
       优势： 不需要安装中间件。可以实现本机消息持久化。支持多个进程或多个不同次启动那个的脚本共享任务。
       劣势： 只能单机共享任务。 无法多台机器共享任务。分布式能力有限。
       
       redis 作为消息队列，
       优势： 真分布式，多个脚本和多态机器可以共享任务。
       劣势： 需要安装redis。 是基于redis的list数组结构实现的，不是真正的ampq消息队列，
              不支持消费确认，所以你不能在程序运行中反复随意将脚本启动和停止或者反复断电断网，
              这样会丢失一部分正在运行的消息任务，断点接续能力弱一些。
       
       mongo 作为消息队列：
       优势： 真分布式。是使用mongo col里面的的一行一行的doc表示一个消息队列里面的一个个任务。支持消费确认。
       劣势： mongo本身没有消息队列的功能，是使用三方包mongo-queue模拟的消息队列。性能没有专用消息队列好。
       
       rabbitmq 作为消息队列：
       优势： 真正的消息队列。支持分布式。支持消费确认，支持随意关闭程序和断网断电。连金融支付系统都用这个，可靠性极高。完美。
       劣势： 大多数人没安装这个中间件，需要学习怎么安装rabbitmq，或者docker安装rabbitmq。
       
       kafka 作为消息队列：
       优势：性能好吞吐量大，中间件扩展好。kafka的分组消费设计得很好，
            还可以随时重置偏移量，不需要重复发布旧消息。
       劣势：和传统mq设计很大的不同，使用偏移量来作为断点接续依据，需要消费哪些任务不是原子性的，
            偏移量太提前导致部分消息重复消费，太靠后导致丢失部分消息。性能好需要付出可靠性的代价。
            高并发数量时候，主题的分区如果设置少，确认消费实现难，框架中采用自动commit的方式。
            要求可靠性 一致性高还是用rabbitmq好。
            
       nsq 作为消息队列：
       优势：部署安装很简单，比rabittmq和kafka安装简单。性能不错。
       劣势：用户很少，比rabbitmq用户少了几百倍，导致资料也很少，需要看nsq包的源码来调用一些冷门功能。
       
```
 
 #### 5.5 比celery有哪些功能优点。
 ```
   答： 1） 如5.4所写，新增了python内置 queue队列和 基于本机的此计划消息队列。不需要安装中间件，即可使用。
        2） 性能比celery框架提高一丝丝。
        3） 公有方法，需要被用户调用的方法或函数一律都没有使用元编程，不需要在消费函数上加app.task这样的装饰器。
            例如不 add.delay(1,2)这样发布任务。 不使用字符串来import 一个模块。
            过多的元编程过于动态，降低不仅会性能，还会让ide无法补全提示，动态一时爽，重构火葬场不是没原因的。
        4） 全部公有方法或函数都能在pycharm下只能提示补全参数名称和参数类型。
            一切为了调用方便，例如get_consumer函数和AbstractConsumer的入参完全重复了，本来事项的时候可以使用*args **kwargs来省略入参，
            但这样会造成ide不能补全提示，此框架一切写法只为给调用者带来使用上的方便。不学celery让用户不知道传什么参数。
            如果拼错了参数，pycharm会显红，大大降低了用户调用出错概率。
         5）不使用命令行启动，在cmd打那么长的一串命令，容易打错字母。并且让用户不知道如何正确的使用celery命令，不友好。
            此框架是直接python xx.py 就启动了。
         6）框架不依赖任何固定的目录结构，无结构100%自由，想把使用框架写在哪里就写在哪里，写在10层级的深层文件夹下都可以。
            脚本可以四处移动改名。celery想要做到这样，要做额外的处理。
         7）使用此框架比celery更简单10倍，如例子所示。使用此框架代码绝对比使用celery少几十行。
         8）消息中间件里面存放的消息任务很小，简单任务 比celery的消息小了50倍。 消息中间件存放的只是函数的参数，辅助参数由consumer自己控制。
            消息越小，中间件性能压力越小。
         9）由于消息中间件里面没有存放其他与python 和项目配置有关的信息，这是真正的跨语言的函数调度框架。
            java人员也可以直接使用redis类rabbitmq类，发送jso参数到中间件，由python消费。celery里面的那种参数，高达几十项
            和项目配置混合了，java人员绝对拼凑不出来这种格式的消息结构。
         10）简单利于团队推广，不需要看复杂的celry 那样的5000页英文文档。
            
 ```


#### 5.6 框架是使用什么序列化协议来序列化消息的。

 ```
    答：框架默认使用json。并且不提供序列化方式选择，有且只能用json序列化。json消息可读性很强，远超其他徐内化方式。
    默认使用json来序列化和反序列化消息。所以推送的消息必须是简单的，不要把一个自定义类型的对象作为消费函数的入参，
    json键的值必须是简单类型，例如 数字 字符串 数组 字典这种。不可以是不可被json序列化的自定义类型的对象。
    
    用json序列化已经满足所有场景了，picke序列化更强，但仍然有一些自定义类型的对象的实例属性由于是一个不可被序列化
    的东西，picke解决不了，这种东西例如self.r = Redis（）  ,不可以序列化，就算能序列化也是要用一串很长的东西来
    表示这种属性，导致中间件要存储很大的东西传输效率会降低，这种完全可以使用json来解决，
    例如指定ip 和端口，在消费函数内部来使用redis。所以用json一定可以满足一切传参场景。
    
    如果json不能满足你的消费任务的序列化，那不是框架的问题，一定是你代码设计的问题。所以不打算准备加入其他序列化方式。
  ```
  

#### 5.6 框架如何实现定时？

 ```
    答：没有定时功能。
        安装三方shchduler框架，消费进程常驻后台，shchduler框架定时推送一个任务到消息队列，定时推送了消息自然就能定时消费。
  ```
  
#### 5.7 为什么强调是函数调度框架不是类调度框架？你代码里面使用了类，是不是和此框架水火不容了?
 ```
    答：一切对类的调用最后都是体现在对方法的调用。这个问题莫名其妙。
    celery rq huery 框架都是针对函数。
    调度函数而不是类是因为：
    1）类实例化时候构造方法要传参，类的公有方法也要传参，这样就不确定要把中间件里面的参数哪些传给构造方法哪些传给普通方法了。
       见5.8
    2） 这种分布式一般要求是幂等的，传啥参数有固定的结果，函数是无依赖状态的。类是封装的带有状态，方法依赖了对象的实例属性。
    
    框架如何调用你代码里面的类。
    假设你的代码是：
    class A():
       def __init__(x):
           self.x = x
        
       def add(y):
           print( self.x + y)
    
    那么你需要再写一个函数
    def your_task(x,y):
        return  A(x).add(y)
    然后把这个函数传给框架就可以了。所以此框架和你在项目里面写类不是冲突的。
  ```
  
  #### 5.8 是怎么调度一个函数的。
 ```
     答：基本原理如下
     
     def add(a,b):
         print(a + b)
         
     从消息中间件里面取出参数{"a":1,"b":2}
     然后使用  add(**{"a":1,"b":2}),就是这样运行函数的。
  ```
  #### 5.9 框架适用哪些场景？
 ```
      答：分布式 、并发、 控频、断点接续运行、定时、指定时间不运行、
          消费确认、重试指定次数、重新入队、超时杀死、计算消费次数速度、预估消费时间、
          函数运行日志记录、任务过滤、任务过期丢弃等数十种功能。
         
          只需要其中的某一种功能就可以使用这。即使不用分布式，也可以使用python内置queue对象。
          这就是给函数添加几十项控制的超级装饰器。是快速写代码的生产力保障。

  ```
  
  #### 5.10 怎么引入使用这个框架？
   ```
    答：先写自己的函数（类）来实现业务逻辑需求，不需要思考怎么导入框架。
        写好函数后把 函数和队列名字绑定传给消费框架就可以了。一行代码就能启动分布式消费。
        RedisConsmer('queue_name',consuming_function=your_function).start_consuming_message()
        所以即使你不想用这个框架了，你写的your_function函数代码并没有作废。
        所以不管是引入这个框架 、废弃使用这个框架、 换成celery框架，你项目的99%行 的业务代码都还是有用的，并没有成为废物。
  ```
   
  
  #### 5.11 怎么写框架？
   ```
    答：需要学习真oop和36种设计模式。
        如果有杠精不信不服这句话的，你觉得可以使用纯函数编程，使用0个类来实现这样的框架。
        
        如果完全不理会设计模式，实现threding gevent evenlet 3种并发模式，加上9种中间件类型，实现分布式消费流程，
        需要反复复制粘贴扣字27次。代码绝对比你这个多。例如基于nsq消息队列实现任务队列框架，加空格只用了80行。如果完全反对oop，
        需要多复制好几千行来实现。
        
        你来写完包括完成10种中间件和3种并发模式，并且预留消息中间件的扩展。
        
        然后我们来和此框架 比较 实现框架难度上、 实现框架的代码行数上、 用户调用的难度上 这些方面。
  ```
   

# 6.更新记录。
## 6.1 新增第十种Consumer，以redis为中间件，但增加了消费确认，是RedisConsumerAckAble类。
```
支持运行过程中，随意关闭和启动python程序。无惧反复关闭python和 突然断电导致任务丢失几百个。

之前开100线程/协程的话，随意重启python和断电会导致极大概率丢失200个任务。

官方Threadpoolexecutor是无界队列。使用这个会导致丢失无数个任务，
因为他会迅速把redis的消息全部取出来，添加到自己的queue队列慢慢消费。
因为这个原因所以需要自定义写BoundedThreadpoolexecutor和CustomThreadpoolexecutor。 v       

改版的CustomThreadpoolexecutor修改成了queue最大长度是max_works，自己内部存储100个，
运行中100个，突然关闭python会丢失200个任务。如果queue设置大小为0，则只会丢失100个运行中的任务。

巧妙的使用redis zset结构作为任务缓冲，value为消息，score为时间戳，具有很好的按时间范围查询和删除功能。
600秒内还没确认重回队列，时间可以配置，左右类似于rabbitmq和nsq的heartbeat_interval作用。

RedisConsumerAckAble类比RedisConsumer会有一丝丝性能损耗。
k8s生产环境一般不需要随意反复重启和随意断电。但还是要写这个类。
redis要是能直接作为mq使用，redis早就一统天下了，哪里还不断有几十种mq出来。
所以直接基于redis list的必须改进。
```

## 6.2 新增基于以redis为消息中间件时候的页面管理和消费速度显示。
```
基于redisboard，但对redis的list模拟mq功能，进行页面显示优化突出消息队列消费，
加黄显示正在运行中的队列和每10秒的消费速度。每隔10秒自动刷新统计。

由于实时发布和消费，例如10秒内发布20个，消费50个，页面只能显示大小降低了30个，
这个只有专业的mq才能分别显示出来，redis list只是简单数组。

rabbitmq nsq都有官方自带速率显示。
```
![Image text](https://i.niupic.com/images/2019/08/26/_122.png)