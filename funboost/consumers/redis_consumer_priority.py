# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
"""

这个是加强版的可确认消费的redis消费实现，所以比redis_conusmer实现复杂很多。
这个可以确保随意反复多次停止重启脚本，任务不丢失，没人采用lua，随意反复重启代码极小概率丢失一个任务。

这个是支持任务优先级的redis队列实现。
"""
import json
import time

import redis3

from funboost.consumers.redis_consumer_ack_able import RedisConsumerAckAble


class RedisPriorityConsumer(RedisConsumerAckAble):
    """
       使用多个redis list来实现redis支持队列优先级。brpop可以支持监听多个redis键。
       根据消息的 priroty 来决定发送到哪个队列。我这个想法和celery依赖的kombu实现的redis具有队列优先级是一样的。

       注意：  rabbitmq、celery队列优先级都指的是同一个队列中的每个消息具有不同的优先级，消息可以不遵守先进先出，而是优先级越高的消息越先取出来。
              队列优先级其实是某个队列中的消息的优先级，这是队列的 x-max-priority 的原生概念。

              队列优先级有的人错误的以为是 queuexx 和queueyy两个队列，以为是优先消费queuexx的消息，这是大错特错的想法。
              队列优先级是指某个队列中的每个消息可以具有不同的优先级，不是在不同队列名之间来比较哪个队列名具有更高的优先级。
    """
    """用法如下。
    第一，如果使用redis做支持优先级的消息队列， @boost中要选择 broker_kind = BrokerEnum.REDIS_PRIORITY
    第二，broker_exclusive_config={'x-max-priority':4} 意思是这个队列中的任务消息支持多少种优先级，一般写5就完全够用了。
    第三，发布消息时候要使用publish而非push,发布要加入参  priority_control_config=PriorityConsumingControlConfig(other_extra_params={'priroty': priorityxx})，
         其中 priorityxx 必须是整数，要大于等于0且小于队列的x-max-priority。x-max-priority这个概念是rabbitmq的原生概念，celery中也是这样的参数名字。

         发布的消息priroty 越大，那么该消息就越先被取出来，这样就达到了打破先进先出的规律。比如优先级高的消息可以给vip用户来运行函数实时，优先级低的消息可以离线跑批。

    from funboost import register_custom_broker, boost, PriorityConsumingControlConfig,BrokerEnum

    @boost('test_redis_priority_queue3', broker_kind=BrokerEnum.REDIS_PRIORITY, qps=5,concurrent_num=2,broker_exclusive_config={'x-max-priority':4})
    def f(x):
        print(x)


    if __name__ == '__main__':
        for i in range(1000):
            randx = random.randint(1, 4)
            f.publish({'x': randx}, priority_control_config=PriorityConsumingControlConfig(other_extra_params={'priroty': randx}))
        print(f.get_message_count())
        f.consume()
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'x-max-priority': None}  # x-max-priority 是 rabbitmq的优先级队列配置，必须为整数，强烈建议要小于5。为None就代表队列不支持优先级。

    def _shedual_task0000(self):

        while True:
            # task_str_list = script(keys=[queues_str, self._unack_zset_name], args=[time.time()])
            task_tuple = self.redis_db_frame_version3.blpop(keys=self.publisher_of_same_queue.queue_list, timeout=60)  # 监听了多个键名，所以间接实现了优先级，和kombu的redis 支持优先级的设计思路不谋而合。
            if task_tuple:
                msg = task_tuple[1]
                self.redis_db_frame_version3.zadd(self._unack_zset_name, {msg: time.time()})
                self.logger.debug(task_tuple)
                self._print_message_get_from_broker('redis', msg)
                # self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：  {task_str_list}  ')
                task_dict = json.loads(msg)
                kw = {'body': task_dict, 'task_str': msg}
                self._submit_task(kw)

    def _shedual_task(self):
        """https://redis.readthedocs.io/en/latest/advanced_features.html#default-pipelines """
        while True:
            # task_str_list = script(keys=[queues_str, self._unack_zset_name], args=[time.time()])
            while True:
                try:
                    with self.redis_db_frame_version3.pipeline() as p:
                        p.watch(self._unack_zset_name, *self.publisher_of_same_queue.queue_list, )
                        task_tuple = p.blpop(keys=self.publisher_of_same_queue.queue_list, timeout=60)  # 监听了多个键名，所以间接实现了优先级，和kombu的redis 支持优先级的设计思路不谋而合。
                        # print(task_tuple)
                        if task_tuple:
                            msg = task_tuple[1]
                            p.zadd(self._unack_zset_name, {msg: time.time()})
                            # self.logger.debug(task_tuple)
                            p.unwatch()
                            p.execute()
                            break
                except redis3.WatchError:
                    continue
            if task_tuple:
                self._print_message_get_from_broker('redis', msg)
                # self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：  {task_str_list}  ')
                task_dict = json.loads(msg)
                kw = {'body': task_dict, 'task_str': msg}
                self._submit_task(kw)

    def _requeue(self, kw):
        self.publisher_of_same_queue.publish(kw['body'])
