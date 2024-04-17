
## 使用单个机器模拟实现用户的如下奇葩特殊需求


```
现在是在单台机器模拟实现  "两个机器轮流运行消息,并且同时只有一台机器在执行消息,同时只有一个消息被执行,不允许并发运行消息 " 这个需求.

实际上是动态自动获取当前机器ip,不需要 run_execute_msg_on_host101.py run_execute_msg_on_host102.py 两个重复的文件

```

## 脚本说明
```
run_distribute_msg.py 是 从queue1 获取消息,并轮流分发到 queue2的各个ip对应的队列名字

run_execute_msg_on_host101.py 和 run_execute_msg_on_host102.py 是为了方便单台机器模拟在两台机器上运行.
```