**`funboost` vs `celery` 性能对比测试结论**

### 2.6.1 `funboost` vs `celery` 控制变量法说明

使用经典的控制变量法测试

共同点是：

在win11 + python3.9 +  本机redis 中间件 + amd r7 5800h cpu 环境下测试 + 选择单线程并发模式 + 相同逻辑消费函数

区别点是：

`funboost` 和 `celery 5.xx`


### 2.6.2 `funboost` vs `celery` 发布性能对比

`funboost`:  发布10万条消息耗时5秒，每隔0.05秒发布1000条,平均每秒发布20000条         

`celery`: 发布10万条消息耗时110秒，每隔1.1秒发布1000条，平均每秒发布900条

对比结果: `funboost`发布性能约为`celery`的22倍

### 2.6.3 `funboost` vs `celery` 消费性能对比

`funboost`: 平均每隔0.07秒消费1000条消息，每秒消费约14000条

`celery`: 平均每隔3.6秒消费1000条消息，每秒消费约300条

对比结果: `funboost`消费性能约为`celery`的46倍

### 2.6.4 `funboost` vs `celery` 总体性能对比

`funboost`在同样的硬件环境和测试条件下（win11 + python3.9 + 本机redis中间件 + AMD R7 5800H CPU + 单线程并发模式 + 相同消费函数），\
无论是在消息发布还是消费方面都大幅优于`celery`，`funboost`是`celery`的发布性能是`22`倍，`funboost` 消费性能是`celery`的`46`倍 ，\
所以`funboost`性能不是比`celery`高百分之多少这种级别,而是高了一个数量级，`funboost`性能是毫无争议的绝对的遥遥领先。