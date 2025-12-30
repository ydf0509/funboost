import time
import redis
from funboost import boost, BrokerEnum, BoosterParams, EmptyConsumer, EmptyPublisher, funboost_config_deafult

'''
使用 Redis 作为消息队列的中间件实现，通过指定 consumer_override_cls 和 publisher_override_cls 为用户自定义的类来实现新增消息队列种类。
'''

class MyRedisConsumer(EmptyConsumer):
    def custom_init(self):
        """初始化 Redis 客户端"""
        print(funboost_config_deafult.BrokerConnConfig.REDIS_URL)
        self.redis_client = redis.from_url(funboost_config_deafult.BrokerConnConfig.REDIS_URL)

    def _dispatch_task(self):
        """从 Redis 队列中消费消息"""
        while True:
            try:
                # 使用 brpop 阻塞式地从队列中获取消息
                _, msg_bytes = self.redis_client.brpop(self.queue_name)
                msg = msg_bytes.decode('utf-8')
                # 提交任务给 funboost 处理
                self._submit_task({'body': msg})
            except redis.exceptions.ConnectionError as e:
                print(f"Redis 连接错误: {e}")
                time.sleep(5)  # 发生连接错误时等待一段时间后重试
            except Exception as e:
                print(f"消息消费过程中发生错误: {e}")
                time.sleep(1)

    def _confirm_consume(self, kw):
        """确认消费（此处为演示，未实现）"""
        pass

    def _requeue(self, kw):
        """将消息重新放回队列"""
        self.redis_client.lpush(self.queue_name, kw['body'])


class MyRedisPublisher(EmptyPublisher):
    def custom_init(self):
        """初始化 Redis 客户端"""
        self.redis_client = redis.from_url(funboost_config_deafult.BrokerConnConfig.REDIS_URL)

    def _publish_impl(self, msg: str):
        """将消息发布到 Redis 队列"""
        self.redis_client.lpush(self.queue_name, msg)

    def clear(self):
        """清空队列"""
        self.redis_client.delete(self.queue_name)

    def get_message_count(self):
        """获取队列中的消息数量"""
        return self.redis_client.llen(self.queue_name)

    def close(self):
        """关闭 Redis 连接"""
        self.redis_client.connection_pool.disconnect()


'''
完全重新自定义增加中间件时，broker_kind 建议指定为 BrokerEnum.EMPTY
'''

@boost(BoosterParams(
    queue_name='test_define_redis_queue',  # 队列名称
    broker_kind=BrokerEnum.REDIS,  # 使用 Redis 作为中间件
    concurrent_num=1,  # 并发数
    consumer_override_cls=MyRedisConsumer,  # 自定义消费者类
    publisher_override_cls=MyRedisPublisher,  # 自定义发布者类
    is_show_message_get_from_broker=True  # 显示从中间件获取的消息
))
def cost_long_time_fun(x):
    """一个耗时函数示例"""
    print(f'开始处理 {x}')
    time.sleep(2)  # 模拟耗时操作
    print(f'结束处理 {x}')


if __name__ == '__main__':
    # 推送 10 个任务到队列
    for i in range(10):
        cost_long_time_fun.push(i)
    # 开始消费队列中的任务
    cost_long_time_fun.consume()