"""
此代码演示 funboost 强大的 消息格式兼容能力, 能消费一切任意队列中已存在的不规范格式的消息(消息格式不是json也能消费),
无论你是否使用funboost来发布消息,无视你的消息是不是json格式,funboost一样能消费.
通过用户自定义 _user_convert_msg_before_run 清洗转化消息成字典或者json字符串,funboost就能消费任意消息.
这是个小奇葩需求,但是funboost在消费任意消息的简单程度这方面能吊打celery
"""

import typing
import redis
from funboost import BrokerEnum, BoosterParams, AbstractConsumer


class MyAnyMsgConvetConsumer(AbstractConsumer):
    def _user_convert_msg_before_run(self, msg) -> typing.Union[dict,str]:
        # 'a=1,b=2' 例如从这个字符串,提取出键值对,返回字典,以适配funboost消费
        new_msg_dict = {}
        msg_split_list = msg.split(',')
        for item in msg_split_list:
            key, value = item.split('=')
            new_msg_dict[key] = int(value)
        self.logger.debug(f'原来消息是:{msg},转换成的新消息是:{new_msg_dict}')  # 例如 实际会打印 原来消息是:a=3,b=4,转换成的新消息是:{'a': 3, 'b': 4}
        return new_msg_dict


@BoosterParams(queue_name="task_queue_consume_any_msg", broker_kind=BrokerEnum.REDIS,
               consumer_override_cls=MyAnyMsgConvetConsumer  # 这行是关键,MyAnyMsgConvetConsumer类自定义了_user_convert_msg_before_run,这个方法里面,用户可以自由发挥清洗转化消息
               )
def task_fun(a: int, b: int):
    print(f'a:{a},b:{b}')
    return a + b


if __name__ == "__main__":
    redis_conn = redis.Redis(db=7)  # 使用原生redis来发布消息，funboost照样能消费。

    redis_conn.lpush('task_queue_consume_any_msg', 'a=1,b=2')  # 模拟别的部门员工,手动发送了funboost框架无法识别的消息格式,原本funboost需要消息是json,但别的部门直接发字符串到消息队列中了.,
    task_fun.publisher.send_msg('a=3,b=4')  # 使用send_msg 而非push和publish方法,是故意发送不规范消息, 就是发送原始消息到消息队列里面,funboost不会去处理添加任何辅助字段发到消息队列里面,例如task_id 发布时间这些东西.

    task_fun.consume()  # funboost 现在可以消费消息队列里面的不规范消息了,因为用户在_user_convert_msg_before_run清洗了消息
