**funboost vs celery 性能对比测试结论**

### 2.6.1 funboost vs celery 控制变量法说明

使用经典的控制变量法测试

共同点是：

在win11 + python3.9 +  redis 中间件 + amd r7 5800h cpu 环境下测试 + 选择单线程并发模式 + 相同逻辑消费函数

区别点是：

funboost 和 celery 5


### 2.6.2 funboost vs celery 发布性能对比

funboost: 发布10万条消息耗时9秒，每隔0.08秒发布1000条，平均每秒发布11000条

celery: 发布10万条消息耗时110秒，每隔1.1秒发布1000条，平均每秒发布900条

对比结果: funboost发布性能约为celery的12倍

### 2.6.3 funboost vs celery 消费性能对比

funboost: 平均每隔0.15秒消费1000条消息，每秒消费约7000条

celery: 平均每隔3.6秒消费1000条消息，每秒消费约300条

对比结果: funboost消费性能约为celery的23倍

### 2.6.4 funboost vs celery 总体性能对比

funboost在同样的硬件环境和测试条件下（win11 + python3.9 + redis中间件 + AMD R7 5800H CPU + 单线程并发模式 + 相同消费函数），无论是在消息发布还是消费方面都大幅优于celery，都超过1000% ，所以 celery性能比funboost性能差了一个数量级，funboost性能是绝对的遥遥领先。