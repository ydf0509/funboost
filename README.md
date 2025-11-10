
# 1.python万能分布式函数调度框架简funboost简介  

funboost快速了解：[https://ydf0509.github.io/funboost_git_pages/funboost_promo.html](https://ydf0509.github.io/funboost_git_pages/funboost_promo.html)

funboost教程: [https://funboost.readthedocs.io/zh-cn/latest/index.html](https://funboost.readthedocs.io/zh-cn/latest/index.html)  

## 1.0 funboost 框架说明介绍

`funboost`是一个 万能 强大 简单  自由 的 `python` 全功能分布式调度框架,它的作用是给用户任意项目的任意函数赋能.

<iframe src="https://ydf0509.github.io/funboost_git_pages/index2.html" width="100%" height="2400" style="border:none;"></iframe>


<h4>📹 观看 funboost 视频</h4>
<video controls width="800" 
      src="https://ydf0509.github.io/funboost_git_pages/%E8%A7%86%E9%A2%91-Funboost_%E8%A7%86%E9%A2%91.mp4">
   您的浏览器不支持视频播放。
</video>

<h4>🎧 收听 funboost 音频</h4>
<audio controls 
      src="https://ydf0509.github.io/funboost_git_pages/%E9%9F%B3%E9%A2%91-funboost_%E9%9F%B3%E9%A2%91.mp4">
   您的浏览器不支持音频播放。
</audio>

#### 快速了解和上手funboost，直接看[1.3例子](#13-框架使用例子)


### 1.0.0 funboost 框架安装方式  

```  
pip install funboost --upgrade  

或 pip install funboost[all]  一次性安装所有小众三方中间件  
```  


###  1.0.1 funboost 功能作用

`funboost` 是一个万能分布式函数调度框架,是用于给用户任意新旧项目的任何函数赋能.   
用户的函数只要加上 `@boost` 装饰器,就能轻松实现分布式函数调度.    
自动支持 40种 消息队列 + 30种任务控制功能 + `python`中所有的并发执行方式


`funboost`的功能是全面性重量级，用户能想得到的功能99%全都有;`funboost`的使用方式是轻量级，只有`@boost`一行代码需要写。    
`funboost`的神奇之处在于它同时拥有"轻量级使用方式"和"重量级功能集"，完全颠覆了"功能强大=使用复杂"的传统思维。   
它证明了一个框架可以既功能丰富又极其易用，这是对传统Python框架设计的一次巧妙超越。   
只需要一行`@boost`代码即可分布式执行`python`一切任意函数，99%用过`funboost`的`pythoner` 感受是 方便 高速 强大 自由。    



#### funboost的适用场景:   
```
`funboost`是python函数加速器，框架包罗万象，一统编程思维，兼容50% `python`编程业务场景，适用范围广,任何新老项目都能用到。    
`funboost` 用途概念就是常规经典的 生产者 + 消息队列中间件 + 消费者 编程思想。  
```

```
需要分布式?  好,funboost支持40多种消息队列,任何只要是稍微小有名气的消息队列和甚至任务框架,funboost全都支持.
需要并发？ 好，那就把Python所有的并发模式（线程、协程、多进程）都给你，并且让它们可以叠加。
需要可靠性？ 好，那就把消费确认（ACK）、自动重试、死信队列（DLQ）、断点续爬做到极致，让你无惧任何宕机。
需要控制力？ 好，那就给你精准的QPS控频、分布式控频、定时任务、延时任务、超时杀死、任务过滤等三十多种控制武器。
需要监控？ 好，那就给你一个开箱即用的Web UI，让你对任务状态、队列情况、消费者实例了如指掌。
需要自由？ 好，那就让你用最普通的Python函数，不侵入你的代码，不规定你的项目结构，让你随时能用，随时能走。
```

#### 有人问 funboost 是做什么的? 怎么回答最合适? 

这个问题很难精确的一句话概括回答,因为funboost是万能框架，几乎所有的python编程业务场景都能用到,答案是发散的不是唯一的。   

发散的答案, 见文档 6.0b 章节  [https://funboost.readthedocs.io/zh-cn/latest/articles/c6.html#b-funboost](https://funboost.readthedocs.io/zh-cn/latest/articles/c6.html#b-funboost)


#### 最最最重要的第一个问题: "funboost这个框架怎么样呀，值得我学习使用吗?"

如果选择学习使用了一个 用途狭窄 功能不好 性能不好 用法复杂 写法不自由 的框架,简直是浪费时间浪费生命.  

问题答案, 见文档 6.0 章节  [https://funboost.readthedocs.io/zh-cn/latest/articles/c6.html#funboost](https://funboost.readthedocs.io/zh-cn/latest/articles/c6.html#funboost)

#### funboost与celery的理念区别 

`funboost`与`celery`关系，如同iphone手机和诺基亚塞班手机，核心本质功能都是通讯打电话，但不能下结论`iphone`是抄袭`诺基亚塞班手机`重复造轮子，`iphone`是重新定义了轮子。    
正如 `iphone` 让`塞班`成为历史，`funboost` 正在让`框架奴役`成为过去。

**共同点:**
```
`Celery` 是一个基于分布式消息队列的 异步任务队列/任务调度框架，用于在后台并发执行耗时任务、定时任务和分布式任务处理。
说得更归根结底就是 `生产者 + broker + 消费者` 普通的编程思想.        
如果你想一句话简单粗暴的概括`funboost`的作用,也可以套用`celery`的这个功能简介,但是区别也很大.  
```

**区别:**
```
`celery`是`围绕celery框架组织代码,属于重型奴役框架`,你围绕`celery`项目结构和`celery app`这样中央app实例 转,去新增定义`@app.task`函数, 
app才是一等公民,task函数是二等公民  

`funboost`是`函数增强器,属于轻型自由框架`,你可以对任意项目任意位置的新旧函数加上`@boost`装饰器,是给你函数赋能插上强大翅膀,
用户不需要围绕`funboost`或某个中央app实例来组织代码结构,用户函数自身就是一等公民   

2个框架最显而易见明显差别就是 `funboost` 无需 `@app.boost` 而是直接`@boost`,这个小区别,造成影响深远的框架用法和理念区别.   
`funboost`任务控制功能更多,支持broker中间件种类更多,并发方式更多,发布性能超越celery 22倍,消费性能超越 celery 46倍,
性能是高几个数量级的断崖式遥遥领先,但反而使用比celery简单得多.
```

#### **funboost 支持的并发模式:**      
`funboost`支持python所有类型的并发模式,支持 `threading` `asyncio` `gevent` `eventlet` `单线程` 并发模式,同时支持 `多进程` 叠加这些细粒度并发模式.

#### **funboost 支持的消息队列中间件:** 
```    
得益于强大的设计,在 `funboost` 中 万物可为`broker`,不仅仅支持了 所有的传统正经消息队列例如 `rabbitmq` `kafka` `nsq`等,   
`funboost`还将各种 `tcp` `grpc` `http`等作为任务队列，   
`funboost` 将各种数据库作为`broker`,包括`redis` `sqlalchemy` `peewee` 作为 `broker`      
`funboost` 将文件系统作为 `broker`,包括 `sqlite` 和 文件夹 作为 `broker`    
并且`funboost` 将 `mysql cdc` 这种`mysql binlog`变化捕获作为`broker`,使得`funboost`可以是事件驱动的,远超`celery`的理念.   
`funboost` 还轻松内置了将各种三方消费框架作为`broker`,例如直接将 `celery` `dramatiq` `huey` `rq` `nameko` 作为`broker`,使用这些框架的核心来执行用户的函数   
```




#### **funboost 学习难吗?**   
```
框架只需要学习`@boost`这一个装饰器的入参就可以，所有用法几乎和1.3例子一摸一样，非常简化简单。 
教程所有例子只是改了下@boost装饰器的入参而已,用户自己可以看装饰器入参解释就行了.

框架对代码没有入侵,可以加到任意已有项目而对项目python文件目录结构0要求,   
不像`celery` `django` `scrapy` 这样的框架,要从一开始就开始规划好项目目录结构,如果不想用框架了,   
或者想改变使用其他框架框架,那么已经所写的代码组织形式就几乎成了废物,需要大改特改.    
但是`funboost`完全不会这样,不管是加上还是去掉`@boost`装饰器,对你的项目影响为0,用户照常使用,   
所以用户可以对任意项目,任意时候,引入使用`funboost`或者删除使用`funboost`,代码组织形式不需要发生变化.   

即使不想用`funboost`了，也不需要亲自去掉`@boost`装饰器，因为函数上面有`@boost`装饰器对函数自身的直接调用运行没有任何影响，  
用户照样可以直接例如 `fun(x,y)`是直接运行函数 ， `fun.push(x,y)` 才是发送到消息队列 
```

"funboost学习和使用难吗?" 的 详细回答可以看文档 `6.0.c` 章节


#### **funboost支持可视化查看和管理消费情况:**    
通过`funboost web manager` 管理系统，支持全面 查看 监控 管理 `funboost`的任务消费。  

#### **funboost的性能超过`celery`一个数量级,不是一个档次上:**    
`funboost`发布性能是`celery`的22倍,`funboost`消费性能是`celery`的46倍! 控制变量法对比方式,见文档2.6章节


#### **funboost框架评价:**  
```     
95%的用户在初步使用后，都表示赞不绝口、相见恨晚、两眼放光。认为`funboost`框架使用简单但功能强大和丰富,   
最重要的是用户使用`funboost`后自己是极端自由的,不像使用其他框架,导致用户编程思维需要发生翻天覆地变化,一切要围绕框架来编程,
`funboost`对用户代码编程思维 入侵是0.  
```

#### **funboost旧框架地址:**       
`funboost`的旧框架名字是`function_scheduling_distributed_framework` , 关系和兼容性见1.0.3介绍。  
旧框架地址： [https://github.com/ydf0509/distributed_framework](https://github.com/ydf0509/distributed_framework)  

## 1.1 github地址和文档地址  

### 1.1.1 分布式函数调度框架文档地址   

[查看分布式函数调度框架文档 https://funboost.readthedocs.io/zh-cn/latest/index.html](https://funboost.readthedocs.io/zh-cn/latest/index.html)  

```
文档很长，大部分都是讲原理和对比各种框架,不仅仅 `how` to use,更多的是 `What` & `Why`。  
但是用户只需要学习1.3这1个例子就能掌握了。因为其他例子只是 @boost的 BoosterParams 里面的控制入参换了一下。  

用户只需要专门看 BoosterParams 里面的每个入参的注释就能掌握框架了，因为funboost只有@boost一行代码需要你写。   
funboost 框架和一般的框架不一样，因为只有一行代码需要掌握，绝对不是要求用户先精通框架本身才能自由发挥。    

只要用过 `funboost` 的用户,都评价比 `celery` 的用法简单几百倍.

用户可以看文档`14`章节,怎么正确的用`ai`大模型掌握`funboost`的用法
```

[**1.python万能分布式函数调度框架简funboost简介**](https://funboost.readthedocs.io/zh-cn/latest/articles/c1.html)  


[**2.funboost对比celery框架**](https://funboost.readthedocs.io/zh-cn/latest/articles/c2.html)  

 
[**3.funboost框架详细介绍**](https://funboost.readthedocs.io/zh-cn/latest/articles/c3.html)


[**4.funboost使用框架的各种代码示例**](https://funboost.readthedocs.io/zh-cn/latest/articles/c4.html)  

 
[**4b.funboost使用框架的各种代码示例(高级进阶)**](https://funboost.readthedocs.io/zh-cn/latest/articles/c4b.html)  


[**5.funboost框架运行时截图**](https://funboost.readthedocs.io/zh-cn/latest/articles/c5.html) 

 
[**6.funboost常见问题回答**](https://funboost.readthedocs.io/zh-cn/latest/articles/c6.html)  

[**7.funboost更新记录**](https://funboost.readthedocs.io/zh-cn/latest/articles/c7.html)  

  
[**8.funboost是万能函数调度框架，当然可以爬虫,自由编程 降维打击 框架奴役**](https://funboost.readthedocs.io/zh-cn/latest/articles/c8.html)  

  
[**9.轻松远程服务器部署运行函数**](https://funboost.readthedocs.io/zh-cn/latest/articles/c9.html)  


[**10.python3.6-3.12 安装/使用funboost出错问题反馈**](https://funboost.readthedocs.io/zh-cn/latest/articles/c10.html)  

 
[**11.funboost 使用某些中间件或三方任务队列框架作为broker的例子(包括celery框架)**](https://funboost.readthedocs.io/zh-cn/latest/articles/c11.html)  


 
[**12.funboost 控制台支持命令行**](https://funboost.readthedocs.io/zh-cn/latest/articles/c12.html)  


[**13.启动 funboost web manager,查看消费结果和队列管理**](https://funboost.readthedocs.io/zh-cn/latest/articles/c13.html)  


#### funboost依赖的nb_log日志文档   
[funboost依赖的nb_log日志文档 https://nb-log-doc.readthedocs.io/zh_CN/latest/articles/c9.html#id2](https://nb-log-doc.readthedocs.io/zh_CN/latest/articles/c9.html#id2)  

```  
文档很长，但归根结底只需要学习 1.3 里面的这1个例子就行，主要是修改下@boost的各种参数，  
通过不同的入参，实践测试下各种控制功能。  
其中文档第四章列举了所有用法举例，  
```  

### 1.1.2 分布式函数调度框架github地址  

[查看分布式函数调度框架github项目](https://github.com/ydf0509/funboost)  



## 1.2 框架功能介绍  


有了这个框架，用户再也无需亲自手写操作进程、线程、协程的并发的代码了。   
有了这个框架，用户再也无需亲自手写操作`redis` `rabbitmq` `socket` `kafka` `celery` `nameko`了。  
有了这个框架,用户再也无法亲自写各种任务控制功能了,`funboost`的任务控制功能应有尽有  

funboost示图：  
![funboost示图](https://s21.ax1x.com/2024/04/29/pkFFghj.png)


也就是这种非常普通的流程图,一样的意思  
![funboost示图](https://s21.ax1x.com/2024/04/29/pkFFcNQ.png)

### 1.2.1 funboost 可以取代 线程池的例子

以下两种方式，都是10线程加python内存queue方式运行f函数，有了此框架，用户无需代码手写手动操作线程 协程 asyncio 进程 来并发。  

1)手动开启线程池方式  

```python  
import time  
from concurrent.futures import ThreadPoolExecutor  


def f(x):  
    time.sleep(3)  
    print(x)  


pool = ThreadPoolExecutor(10)  

if __name__ == '__main__':  
    for i in range(100):  
        pool.submit(f, i)  

```  

2)`funboost` 使用内存队列,设置10线程并发  

```python  
import time  
from funboost import BoosterParams, BrokerEnum  


@BoosterParams(queue_name="test_insteda_thread_queue", broker_kind=BrokerEnum.MEMORY_QUEUE, concurrent_num=10, is_auto_start_consuming_message=True)  
def f(x):  
    time.sleep(3)  
    print(x)  


if __name__ == '__main__':  
    for i in range(100):  
        f.push(i)  


```  


### 1.2.2 funboost支持丰富的任务控制功能

<pre style="color: #A0A000">  
     分布式：  
        支持数十种最负盛名的消息中间件.(除了常规mq，还包括用不同形式的如 数据库 磁盘文件 redis等来模拟消息队列)  

     并发：  
        支持threading gevent eventlet asyncio 单线程 5种并发模式 叠加 多进程。  
        多进程不是和前面四种模式平行的，是叠加的，例如可以是 多进程 + 协程，多进程 + 多线程。  
   
     控频限流：  
        例如十分精确的指定1秒钟运行30次函数或者0.02次函数（无论函数需要随机运行多久时间，都能精确控制到指定的消费频率；  
   
     分布式控频限流：  
        例如一个脚本反复启动多次或者多台机器多个容器在运行，如果要严格控制总的qps，能够支持分布式控频限流。  
  
     任务持久化：  
        消息队列中间件天然支持  
   
     断点接续运行：  
        无惧反复重启代码，造成任务丢失。消息队列的持久化 + 消费确认机制 做到不丢失一个消息  
        (此框架很重视消息的万无一失，就是执行函数的机器支持在任何时候随时肆无忌惮反复粗暴拉电闸断电，或者强制硬关机，  
        或者直接用锄头把执行函数代码的机器砸掉，只要不是暴力破坏安装了消息队列中间件的机器就行，消息就万无一失，  
        现在很多人做的简单redis list消息队列，以为就叫做分布式断点接续，那是不正确的，因为这种如果把消息从reidis brpop取出来后，  
        如果消息正在被执行，粗暴的kill -9脚本或者直接强制关机，那么正在运行的消息就丢失了，如果是多线程同时并发运行很多消息，粗暴重启  
        会丢失几百个大量消息，这种简单的redis list根本就不能叫做安全的断点续传。  
        分布式函数调度框架的消费确认机制，保证函数运行完了才确认消费，正在运行突然强制关闭进程不会丢失一个消息，  
        下次启动还会消费或者被别的机器消费。  
        此框架的消息万无一失特性，不仅支持rabbbitmq因为原生支持，也支持redis，框架对redis的实现机制是因为客户端加了一层保障)。  
   
     定时：  
        可以按时间间隔、按指定时间执行一次、按指定时间执行多次，使用的是apscheduler包的方式。  
   
     延时任务：  
         例如规定任务发布后，延迟60秒执行，或者规定18点执行。这个概念和定时任务有一些不同。  
    
     指定时间不运行：  
        例如，有些任务你不想在白天运行，可以只在晚上的时间段运行  
   
     消费确认：  
        这是最为重要的一项功能之一，有了这才能肆无忌惮的任性反复重启代码也不会丢失一个任务。  
        （常规的手写 redis.lpush + redis.blpop,然后并发的运行取出来的消息，随意关闭重启代码瞬间会丢失大量任务，  
        那种有限的 断点接续 完全不可靠，根本不敢随意重启代码）  
   
     立即重试指定次数：  
        当函数运行出错，会立即重试指定的次数，达到最大次重试数后就确认消费了  
   
     重新入队：  
        在消费函数内部主动抛出一个特定类型的异常ExceptionForRequeue后，消息重新返回消息队列  
   
     超时杀死：  
        例如在函数运行时间超过10秒时候，将此运行中的函数kill  
   
     计算消费次数速度：  
        实时计算单个进程1分钟的消费次数，在日志中显示；当开启函数状态持久化后可在web页面查看消费次数  
   
     预估消费时间：  
        根据前1分钟的消费次数，按照队列剩余的消息数量来估算剩余的所需时间  
   
     函数运行日志记录：  
        使用自己设计开发的 控制台五彩日志（根据日志严重级别显示成五种颜色；使用了可跳转点击日志模板）  
        + 多进程安全切片的文件日志 + 可选的kafka elastic日志  
         
     任务过滤：  
        例如求和的add函数，已经计算了1 + 2,再次发布1 + 2的任务到消息中间件，可以让框架跳过执行此任务。  
        任务过滤的原理是使用的是函数入参判断是否是已近执行过来进行过滤。  
   
     任务过滤有效期缓存：  
        例如查询深圳明天的天气，可以设置任务过滤缓存30分钟，30分钟内查询过深圳的天气，则不再查询。  
        30分钟以外无论是否查询过深圳明天的天气，则执行查询。  
  
     任务过期丢弃：  
        例如消息是15秒之前发布的，可以让框架丢弃此消息不执行，防止消息堆积,  
        在消息可靠性要求不高但实时性要求高的高并发互联网接口中使用  
      
     函数状态和结果持久化：  
        可以分别选择函数状态和函数结果持久化到mongodb，使用的是短时间内的离散mongo任务自动聚合成批量  
        任务后批量插入，尽可能的减少了插入次数  
            
     消费状态实时可视化：  
        在页面上按时间倒序实时刷新函数消费状态，包括是否成功 出错的异常类型和异常提示   
        重试运行次数 执行函数的机器名字+进程id+python脚本名字 函数入参 函数结果 函数运行消耗时间等  
           
     消费次数和速度生成统计表可视化：  
        生成echarts统计图，主要是统计最近60秒每秒的消费次数、最近60分钟每分钟的消费次数  
        最近24小时每小时的消费次数、最近10天每天的消费次数  
                      
     rpc：  
        生产端（或叫发布端）获取消费结果。各个发布端对消费结果进行不同步骤的后续处理更灵活，而不是让消费端对消息的处理一干到底。  

     远程服务器部署消费函数：  
        代码里面 task_fun.fabric_deploy('192.168.6.133', 22, 'xiaomin', '123456', process_num=2) 只需要这样就可以自动将函数部署在远程机器运行，  
        无需任何额外操作，不需要借助阿里云codepipeline发版工具 和 任何运维发版管理工具，就能轻松将函数运行在多台远程机器。task_fun指的是被@boost装饰的函数  

     暂停消费：  
        支持从python解释器外部/远程机器 ，控制暂停消息消费和继续消费。  

     优先级队列：  
         支持队列优先级消息。  

     远程杀死(取消)任务：  
         支持在发布端杀死正在运行的消息，发送杀死命令时候对还未取出的消息则放弃运行消息。  
  
     funboost支持命令行操作：  
         使用fire实现的命令行，见文档第12章  

     可视化查看和操作：  
         funboost web manager 可以查看和管理队列和消费运行情况。  

</pre>  

关于稳定性和性能，一句话概括就是直面百万c端用户（包括app和小程序）， 已经连续超过三个季度稳定高效运行无事故，从没有出现过假死、崩溃、内存泄漏等问题。 windows和linux行为100%一致，不会像celery一样，相同代码前提下，很多功能在win上不能运行或出错。  

## 1.3 框架使用例子  

使用之前先学习 PYTHONPATH的概念  [https://github.com/ydf0509/pythonpathdemo](https://github.com/ydf0509/pythonpathdemo)  

win cmd和linux 运行时候，设置 PYTHONPATH 为项目根目录，是为了自动生成或读取到项目根目录下的 funboost_config.py文件作为配置。  

```  
以下这只是简单求和例子，实际情况换成任意函数里面写任意逻辑，框架可没有规定只能用于 求和函数 的自动调度并发。  
而是根据实际情况函数的参数个数、函数的内部逻辑功能，全部都由用户自定义，函数里面想写什么就写什么，想干什么就干什么，极端自由。  
也就是框架很容易学和使用，把下面的task_fun函数的入参和内部逻辑换成你自己想写的函数功能就可以了，
框架只需要学习boost这一个函数的参数就行。  
测试使用的时候函数里面加上sleep模拟阻塞，从而更好的了解框架的并发和各种控制功能。  
```  

```  
有一点要说明的是框架的消息中间件的ip 端口 密码 等配置是在你第一次运行代码时候，在你当前项目的根目录下
生成的 funboost_config.py 按需设置 (默认放在项目根目录是为了方便利用项目的 PYTHONPATH。当然，只要 PYTHONPATH 设置正确，  
该配置文件可以放在磁盘的任意文件夹里面。用户可以看教程 6.18.3 问答章节)。  

funboost_config.py 里面仅仅是配置 中间件连接,例如ip 端口这些简单的配置, 只需要第一次配置正确即可,  
后续的开发中基本无需再次修改此文件。 因为所有消费函数任务控制功能都是在 BoosterParams 中传参。  
```  

### 1.3.1 funboost最简单例子  

```python  
import time  
from funboost import boost, BrokerEnum,BoosterParams  

# BoosterParams 代码自动补全请看文档4.1.3  
@boost(BoosterParams(queue_name="task_queue_name1", qps=5, broker_kind=BrokerEnum.SQLITE_QUEUE))  # 入参包括20种，运行控制方式非常多，想得到的控制都会有。  
def task_fun(x, y):  
    print(f'{x} + {y} = {x + y}')  
    time.sleep(3)  # 框架会自动并发绕开这个阻塞，无论函数内部随机耗时多久都能自动调节并发达到每秒运行 5 次 这个 task_fun 函数的目的。  


if __name__ == "__main__":  
    for i in range(100):  
        task_fun.push(i, y=i * 2)  # 发布者发布任务  
    task_fun.consume()  # 消费者启动循环调度并发消费任务  
```  

<pre style="background-color: #BA2121;color: yellow">tips: sqlite作为消息队列,如果linux或mac运行报错read-only文件夹权限,需修改SQLLITE_QUEUES_PATH 就好啦,见文档10.3 </pre>  

**代码说明:**
对于消费函数，框架内部会生成发布者(生产者)和消费者。  
1.推送。 `task_fun.push(1,y=2)` 会把 `{"x":1,"y":2}` (消息也自动包含一些其他辅助信息) 发送到中间件的 `task_queue_name1` 队列中。   
2.消费。 `task_fun.consume()` 开始自动从中间件拉取消息，并发的调度运行函数，`task_fun(**{"x":1,"y":2})`,每秒运行5次   
整个过程只有这两步，清晰明了，其他的控制方式需要看 boost 的中文入参解释，全都参数都很有用。   

这个是单个脚本实现了发布和消费，一般都是分离成两个文件的，任务发布和任务消费无需在同一个进程的解释器内部，  
因为是使用了中间件解耦消息和持久化消息，不要被例子误导成了，以为发布和消费必须放在同一个脚本里面  

框架使用方式基本上只需要练习这一个例子就行了，其他举得例子只是改了下broker_kind和其他参数而已，  
而且装饰器的入参已近解释得非常详细了，框架浓缩到了一个装饰器，并没有用户需要从框架里面要继承什么组合什么的复杂写法。  
用户可以修改此函数的`sleep`大小和`@boost`的数十种入参来学习 验证 测试框架的功能。  
  

控制台运行截图:  
发布:
![pkFkP4H.png](https://s21.ax1x.com/2024/04/29/pkFkP4H.png)

消费:
![pkFkCUe.png](https://s21.ax1x.com/2024/04/29/pkFkCUe.png)


### 1.3.2 funboost集中演示一个功能更多的综合例子  

```python  


"""  
一个展示更全面 funboost 用法的例子  
包含了  
1.继承BoosterParams，为了每个装饰器少写入参  
2.rpc获取结果  
3.连续丝滑启动多个消费函数  
4.定时任务  
"""  
from funboost import boost, BrokerEnum,BoosterParams,ctrl_c_recv,ConcurrentModeEnum,ApsJobAdder  
import time  

class MyBoosterParams(BoosterParams):  # 自定义的参数类，继承BoosterParams，用于减少每个消费函数装饰器的重复相同入参个数  
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE  
    max_retry_times: int = 3  
    concurrent_mode: str = ConcurrentModeEnum.THREADING   

  
@boost(MyBoosterParams(queue_name='s1_queue', qps=1,   
                    #    do_task_filtering=True, # 可开启任务过滤，防止重复入参消费。  
                       is_using_rpc_mode=True, # 开启rpc模式，支持rpc获取结果  
                       ))  
def step1(a:int,b:int):  
    print(f'a={a},b={b}')  
    time.sleep(0.7)  
    for j in range(10):  
        step2.push(c=a+b +j,d=a*b +j,e=a-b +j ) # step1消费函数里面，也可以继续向其他任意队列发布消息。  
    return a+b  


@boost(MyBoosterParams(queue_name='s2_queue', qps=3,   
                      max_retry_times=5,# 可以在此覆盖MyBoosterParams中的默认值，例如为step2单独设置最大重试次数为5  
))   
def step2(c:int,d:int,e:int=666):  
    time.sleep(3)  
    print(f'c={c},d={d},e={e}')  
    return c* d * e  


if __name__ == '__main__':  
    step1.clear() # 清空队列  
    step2.clear() # 清空队列  

    step1.consume() # 调用.consume是非阻塞的启动消费，是在单独的子线程中循环拉取消息的。   
    # 有的人还担心阻塞而手动使用 threading.Thread(target=step1.consume).start() 来启动消费，这是完全多此一举的错误写法。  
    step2.consume() # 所以可以在当前主线程连续无阻塞丝滑的启动多个函数消费。  
    step2.multi_process_consume(3) # 这是多进程叠加了多线程消费，另外开启了3个进程，叠加了默认的线程并发。  

    async_result = step1.push(100,b=200)  
    print('step1的rpc结果是：',async_result.result)  # rpc阻塞等待消step1的费结果返回  

    for i in range(100):  
        step1.push(i,i*2) # 向 step1函数的队列发送消息,入参和手动调用函数那样很相似。  
        step1.publish ({'a':i,'b':i*2},task_id=f'task_{i}') # publish 第一个入参是字典，比push能传递更多funboost的辅助参数，类似celery的apply_async和delay的关系。一个简单，一个复杂但强大。  
  
  

    """  
    1.funboost 使用 ApsJobAdder.add_push_job来添加定时任务，不是add_job。  
    2.funboost是轻度封装的知名apscheduler框架，所以定时任务的语法和apscheduler是一样的，没有自己发明语法和入参  
    用户需要苦学apscheduler教程，一切定时都是要学apscheduler知识，定时和funboost知识关系很小。  
    3.funboost的定时任务目的是定时推送消息到消息队列中，而不是定时直接在当前程序中执行某个消费函数。  

    下面是三种方式添加定时任务，这些定时方式都是知名apscheduler包的定时方式，和funboost没关系。  
    """  

   # ApsJobAdder 类可以多次重复实例化,内部对每一个消费函数使用一个单独的apscheduler对象,避免扫描与当前关心的消费函数不相干的redis jobstore中的定时任务  

   # 方式1：指定日期执行一次  
    ApsJobAdder(step2,   
               job_store_kind='redis', # 使用reids作为 apscheduler的 jobstrores  
               is_auto_start=True,   # 添加任务，并同时顺便启动了定时器 执行了apscheduler对象.start()  
    ).add_push_job(  
        trigger='date',  
        run_date='2025-06-30 16:25:40',  
        args=(7, 8,9),  
        id='date_job1',  
        replace_existing=True,  
    )  

    # 方式2：固定间隔执行  
    ApsJobAdder(step2, job_store_kind='redis').add_push_job(  
        trigger='interval',  
        seconds=30,  
        args=(4, 6,10),  
        id='interval_job1',  
        replace_existing=True,  
    )  

    # 方式3：使用cron表达式定时执行  
    ApsJobAdder(step2, job_store_kind='redis').add_push_job(  
        trigger='cron',  
        day_of_week='*',  
        hour=23,  
        minute=49,  
        second=50,  
        kwargs={"c": 50, "d": 60,"e":70},  
        replace_existing=True,  
        id='cron_job1')  
  
    ctrl_c_recv()  # 用于阻塞代码，阻止主线程退出，使主线程永久运行。  相当于 你在代码最末尾，加了个 while 1:time.sleep(10)，使主线程永不结束。apscheduler background定时器守护线程需要这样保持定时器不退出。  

```  

**funboost 上面代码用法小结**:   
`funboost` 鼓励一种`“反框架”`的思维。它告诉你：“你才是主角，我只是你的赋能工具。” 你的函数是独立的、可复用的、可独立运行,独立测试的。  
`@boost` 只是一个可以随时加上或拿掉的“增强插件”。这种设计让你永远不会被框架“绑架”，保持了代码的纯粹性和长久的生命力。  

并且即使你不想用`funboost来`赋能你的函数,也不需要去掉`@boost`装饰器,   
因为 `消费函数.push(1,2)` 和 `消费函数.publish({"x":1, "y":2})` 才是发布到消息队列,  
你直接调用 `消费函数(1,2)` 是不会发布到消息队列的,是直接原始的调用函数本身。  
 
“放荡不羁”的 `funboost`，是以最少的规则，释放了开发者最大的创造力。 它相信优秀的程序员能够自己管理好业务逻辑，  
而框架的职责是赋能你的函数,扫清所有工程化障碍，让你自由驰骋。  



### 1.3.3  funboost的 @BoosterParams(...)  和 @boost(BoosterParams(...)) 等效  

通常代码例子是:  

```python  
@boost(BoosterParams(queue_name="task_queue_consume_any_msg"))  
def task_fun(a: int, b: int):  
    print(f'a:{a},b:{b}')  
    return a + b  
```  

但如果你追求极致简化,也可以写成如下,不要@boost,直接@BoosterParams  

```python  
@BoosterParams(queue_name="task_queue_consume_any_msg")  
def task_fun(a: int, b: int):  
    print(f'a:{a},b:{b}')  
    return a + b  
```  

## funboost web manager 截图：  

函数消费结果：可查看和搜索函数实时消费状态和结果  
[![pEJCffK.png](https://s21.ax1x.com/2025/03/04/pEJCffK.png)](https://imgse.com/i/pEJCffK)  

消费速度图：可查看实时和历史消费速度  
[![pEJCWY6.png](https://s21.ax1x.com/2025/03/04/pEJCWY6.png)](https://imgse.com/i/pEJCWY6)  

运行中消费者 by ip： 根据ip搜索有哪些消费者  
[![pEJCRFx.png](https://s21.ax1x.com/2025/03/04/pEJCRFx.png)](https://imgse.com/i/pEJCRFx)  

队列操作：查看和操作队列，包括 清空清空 暂停消费 恢复消费 调整qps和并发  

<!-- [![pEJC6m9.png](https://s21.ax1x.com/2025/03/04/pEJC6m9.png)](https://imgse.com/i/pEJC6m9) -->  

[![pVSOJcq.png](https://s21.ax1x.com/2025/05/27/pVSOJcq.png)](https://imgse.com/i/pVSOJcq)  

队列操作，查看消费者详情：查看队列的所有消费者详情  
[![pEJCgT1.png](https://s21.ax1x.com/2025/03/04/pEJCgT1.png)](https://imgse.com/i/pEJCgT1)  


队列操作:查看消费曲线图，查看各种消费指标。  
包括 历史运行次数  历史运行失败次数  近10秒完成  近10秒失败  近10秒函数运行平均耗时  累计函数运行平均耗时  剩余消息数量  
[![pVpr7sP.png](https://s21.ax1x.com/2025/05/29/pVpr7sP.png)](https://imgse.com/i/pVpr7sP)  

rpc调用：在网页上对30种消息队列发布消息并获取消息的函数执行结；根据taskid获取结果。  

<!-- [![pETq8hj.png](https://s21.ax1x.com/2025/04/28/pETq8hj.png)](https://imgse.com/i/pETq8hj) -->  

[![pE7y8oT.png](https://s21.ax1x.com/2025/04/29/pE7y8oT.png)](https://imgse.com/i/pE7y8oT)  

## 1.4  python分布式函数执行为什么重要？  

```text  
python比其他语言更需要分布式函数调度框架来执行函数，有两点原因  

1 python有gil，  
  直接python xx.py启动没有包括multipricsessing的代码，在16核机器上，cpu最多只能达到100%,也就是最高使用率1/16，  
  别的语言直接启动代码最高cpu可以达到1600%。如果在python代码里面亲自写多进程将会十分麻烦，对代码需要改造需要很大  
  ，多进程之间的通讯，多进程之间的任务共享、任务分配，将会需要耗费大量额外代码，  
  而分布式行函数调度框架天生使用中间件解耦的来存储任务，使得单进程的脚本和多进程在写法上  
  没有任何区别都不需要亲自导入multiprocessing包，也不需要手动分配任务给每个进程和搞进程间通信，  
  因为每个任务都是从中间件里面获取来的。  
  
2 python性能很差，不光是gil问题，只要是动态语言无论是否有gil限制，都比静态语言慢很多。  
 那么就不光是需要跨进程执行任务了，例如跨pvm解释器启动脚本共享任务(即使是同一个机器，把python xx.py连续启动多次)、  
 跨docker容器、跨物理机共享任务。只有让python跑在更多进程的cpu核心 跑在更多的docker容器 跑在更多的物理机上，  
 python才能获得与其他语言只需要一台机器就实现的执行速度。分布式函数调度框架来驱动函数执行针对这些不同的场景，  
 用代码不需要做任何变化。  
   
所以比其他语言来说，python是更需要分布式函数调度框架来执行任务。  
  
```  

## 1.5 框架学习方式  

```  
把1.3的求和例子，通过修改boost装饰器额参数和sleep大小反复测试两数求和，  
从而体会框架的分布式 并发 控频。  

这是最简单的框架，只有@boost 1行代码需要学习。说的是这是最简单框架，这不是最简单的python包。  
如果连只有一个重要函数的框架都学不会，那就学不会学习得了更复杂的其他框架了，大部分框架都很复杂比学习一个包难很多。  
大部分框架，都要深入使用里面的很多个类，还需要继承组合一顿。  
```  

用户也可以按照 文档14章节的方式,使用ai来掌握`funboost`

## 1.6 funboost支持支持celery框架整体作为funboost的broker (2023.4新增)  

`funboost`通过支持`celery`作为broker_kind,使`celery`框架变成了`funboost`的一个子集  
  
```  
见11.1章节代码例子，celery框架整体作为funboost的broker，funboost的发布和消费将只作为极简api，  
核心的消费调度和发布和定时功能，都是由celery框架来完成，funboost框架的发布和调度代码不实际起作用。  
用户操作funboost的api，语法和使用其他消息队列中间件类型一样，funboost自动化操作celery。  

用户无需操作celery本身，无需敲击celery难记的命令行启动消费、定时、flower;  
用户无需小心翼翼纠结亲自使用celery时候怎么规划目录结构 文件夹命名 需要怎么在配置写include 写task_routes，  
完全不存在需要固定的celery目录结构，不需要手动配置懵逼的任务路由，  
不需要配置每个函数怎么使用不同的队列名字，funboost自动搞定这些。  

用户只需要使用简单的funboost语法就能操控celery框架了。funboost使用celery作为broker_kind,  
远远的暴击亲自使用无法ide下代码补全的celery框架的语法。  
```  



[查看分布式函数调度框架完整文档](https://funboost.readthedocs.io/)  

![](https://visitor-badge.glitch.me/badge?page_id=distributed_framework)  

<div> </div>  

[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  

