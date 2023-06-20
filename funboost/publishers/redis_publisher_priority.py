# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12


from funboost.publishers.redis_publisher_simple import RedisPublisher


class RedisPriorityPublisher(RedisPublisher):
    """
    使用多个redis list来实现redis支持队列优先级。brpop可以支持监听多个redis键。
    根据消息的 priroty 来决定发送到哪个队列。我这个想法和celery依赖的kombu实现的redis具有队列优先级是一样的。

    注意：  rabbitmq、celery队列优先级都指的是同一个队列中的每个消息具有不同的优先级，消息可以不遵守先进先出，而是优先级越高的消息越先取出来。
           队列优先级其实是某个队列中的消息的优先级，这是队列的 x-max-priority 的原生概念。
           队列优先级有的人以为是 queuexx 和queueyy两个队列，以为是优先消费queuexx的消息，这是大错特错的想法。
           队列优先级是指某个队列中的消息具有优先级，不是在不同队列名之间来比较哪个队列具有更高的优先级。
    """
    """用法如下。
    第一，如果使用redis做消息队列， @boost中要选择 broker_kind = REDIS_PRIORITY
    第二，broker_exclusive_config={'x-max-priority':4} 意思是这个队列中的任务消息支持多少种优先级，一般写5就完全够用了。
    第三，发布消息时候要使用publish而非push,发布要加入参  priority_control_config=PriorityConsumingControlConfig(other_extra_params={'priroty': priorityxx})，
         其中 priorityxx 必须是整数，要大于等于0且小于队列的x-max-priority。x-max-priority这个概念是rabbitmq的原生概念，celery中也是这样的参数名字。
         
         发布的消息priroty 越大，那么该消息就越先被取出来，这样就达到了打破先进先出的规律。比如优先级高的消息可以给vip用户来运行函数实时，优先级低的消息可以离线跑批。
    
    @boost('test_redis_priority_queue3', broker_kind=BROKER_KIND_REDIS_PRIORITY, qps=5,concurrent_num=2,broker_exclusive_config={'x-max-priority':4})
    def f(x):
        print(x)
    
    
    if __name__ == '__main__':
        f.clear()
        print(f.get_message_count())
    
        for i in range(1000):
            randx = random.randint(1, 4)
            f.publish({'x': randx}, priority_control_config=PriorityConsumingControlConfig(other_extra_params={'priroty': randx}))
        print(f.get_message_count())
    
        f.consume()
    """

    def custom_init(self):
        queue_list = [self._queue_name]
        x_max_priority = self.broker_exclusive_config['x-max-priority']
        if x_max_priority:
            for i in range(1, x_max_priority + 1):
                queue_list.append(f'{self.queue_name}:{i}')
        queue_list.sort(reverse=True)
        self.queue_list = queue_list

    def build_queue_name_by_msg(self, msg):
        priority = self._get_from_other_extra_params('priroty', msg)
        x_max_priority = self.broker_exclusive_config['x-max-priority']
        queue_name = self.queue_name
        if x_max_priority and priority:
            priority = min(priority, x_max_priority)  # 防止有傻瓜发布消息的优先级priroty比最大支持的优先级还高。
            queue_name = f'{self.queue_name}:{priority}'
        return queue_name

    def concrete_realization_of_publish(self, msg):
        queue_name = self.build_queue_name_by_msg(msg)
        self.logger.debug([queue_name, msg])
        self.redis_db_frame.rpush(queue_name, msg)

    def clear(self):
        self.redis_db_frame.delete(*self.queue_list)
        self.redis_db_frame.delete(f'{self._queue_name}__unack')
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    def get_message_count(self):
        count = 0
        for queue_name in self.queue_list:
            count += self.redis_db_frame.llen(queue_name)
        return count

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass
