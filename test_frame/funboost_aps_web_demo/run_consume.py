from funcs import fun_sum
from funboost import ApsJobAdder,ctrl_c_recv

if __name__ == '__main__':
    """
    这行 ApsJobAdder(fun_sum,job_store_kind='redis',is_auto_paused=False)  很很重要，一定要启动apschduler定时器。即使你不打算添加定时任务，apschduler对象也需要被启动。
    你如果不启动apschduler对象，apschduler对象就不会扫描执行redis中已添加好的的定时任务计划，就不会自动push消息到消息队列中。 fun_sum.consume() 就无任务可执行。
    到时候你又懵逼到处问，为什么已添加到redis中的定时任务不执行了。
    """
    ApsJobAdder(fun_sum,job_store_kind='redis',)  # 这行代码内部帮你启动了 apschduler对象，apschduler对象会扫描redis中的定时任务，并执行定时任务，定时任务的功能就是push消息到消息队列中。

    fun_sum.consume()  # 启动消费消息队列的消息
    ctrl_c_recv()   # 这行很重要，一定要阻止主线程退出，否则主线程退出了， background的apschduler对象就会退出，到时候你又懵逼为什么不执行定时任务了。这些都是apschrudler本身的知识，我就不多说了。