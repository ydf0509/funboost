"""
演示不同的函数，怎么优先消费某个函数。
比如爬虫你想深度优先，那就优先运行爬详情页的函数，把爬详情页函数的优先级调大。
你想广度优先就优先运行爬列表页的函数，把爬列表页页函数的优先级调大。

如下代码就是把f3函数的优先级设置成了3，f2的优先级设置成了2，f1的优先级设置成了1，所以先发布3000个消息到消息队列中，会优先运行f3函数，最后才运行f1函数。
优先级是针对某一个队列而言，不是针对不同队列的优先级，但只要懂得变通，在下面代码的例子中的boost_fun函数这样分发调用不同的函数，就可以实现多个函数之间的优先级了。

运行可以发现控制台先打印的都是f3，最后还是f1.
"""
from funboost import boost, PriorityConsumingControlConfig, BrokerEnum


def f1(x, y):
    print(f'f1  x:{x},y:{y}')


def f2(a):
    print(f'f2  a:{a}')


def f3(b):
    print(f'f3  b:{b}')


@boost('test_priority_between_funs', broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM, qps=100, broker_exclusive_config={'x-max-priority': 5})
def boost_fun(fun_name: str, fun_kwargs: dict, ):
    function = globals()[fun_name]
    return function(**fun_kwargs)


if __name__ == '__main__':
    boost_fun.clear()
    for i in range(1000):
        boost_fun.publish({'fun_name': 'f1', 'fun_kwargs': {'x': i, 'y': i}, },
                          priority_control_config=PriorityConsumingControlConfig(other_extra_params={'priroty': 1}))
        boost_fun.publish({'fun_name': 'f2', 'fun_kwargs': {'a': i, }, },
                          priority_control_config=PriorityConsumingControlConfig(other_extra_params={'priroty': 2}))
        boost_fun.publish({'fun_name': 'f3', 'fun_kwargs': {'b': i, }, },
                          priority_control_config=PriorityConsumingControlConfig(other_extra_params={'priroty': 3}))

    print(boost_fun.get_message_count())
    boost_fun.consume()
