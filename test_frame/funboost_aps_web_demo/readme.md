

### 4.4.3 演示在python web中定时任务的添加 （添加和执行定时任务分在不同的py脚本中）


web中添加定时任务demo连接：

[https://github.com/ydf0509/funboost/tree/master/test_frame/funboost_aps_web_demo](https://github.com/ydf0509/funboost/tree/master/test_frame/funboost_aps_web_demo)

##### 4.4.3.1 演示在python web中定时任务的添加， 添加定时任务的脚本和启动消费的脚本不在同一个py文件中

```
演示在python web中定时任务的添加，添加定时任务的脚本和启动消费的脚本不在同一个py文件中,一定要注意务必要启动定时任务apschduler对象，这是最关键的。
```


#####  4.4.3.2 web_app.py 是web应用，负责添加定时任务到redis中。此处使用flask框架演示， django  fastapi同理，不需要我一一举例子。
```
因为funboost是自由无拘无束的，不需要 django-funboost  flask-funboost fastapi-funboost 插件。

只有坑爹难用的celery才需要django-celery  flask-celery fastapi-celery 三方插件来帮助用户简化适配各种web框架使用，
funboost压根不需要这种适配各种web框架的插件。
```
##### 4.4.3.3 run_consume.py 是启动消费 和 启动apschduler定时器的脚本
```python
ApsJobAdder(fun_sum,job_store_kind='redis',) #负责启动apschduler对象，apschduler对象会扫描redis中的定时任务，并执行定时任务，定时任务的功能就是定时push消息到消息队列中。

fun_sum.consume()  # 启动消费消息队列中的消息
```

**警告！！！你不要只启动fun_sum.consume() 而不启动apschduler对象，否则apschduler对象不会扫描redis中已添加好的定时任务，就不会自动定时的push消息到消息队列中。**







