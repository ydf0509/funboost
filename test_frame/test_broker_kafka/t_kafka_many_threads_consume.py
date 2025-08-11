

"""
从0实现一个 kafka消费类,

支持设置num_threads为很高的数字,这个数字可以远高于分区数
callback_func 是用户传递一个自定义函数, 需要自动在 线程池大小为num_threads 的线程池中执行这个函数

要求:
随时任意kill -9重启程序,做到不丢失 不跳过消息

例如需要避免如下:
消息耗时是随机的,例如msg1耗时100秒,但msg2耗时30秒,msg3耗时10秒,如果msg3提交offset后,
如果突然重启程序,造成msg1和msg2无法再次消费


"""

class KafkaManyThreadsConsumer:
    def __init__(self, kafka_broker_address, topic, group_id, num_threads=100,callback_func=None):
        pass

