# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:32
import json
import time

from function_scheduling_distributed_framework.consumers.base_consumer import AbstractConsumer
from function_scheduling_distributed_framework.consumers.confirm_mixin import ConsumerConfirmMixinWithTheHelpOfRedis


class RedisConsumerAckAble_Old(ConsumerConfirmMixinWithTheHelpOfRedis, AbstractConsumer, ):
    """
    redis作为中间件实现的。将取出来的消息同时放入一个set中，代表unack消费状态。以支持对机器和python进程的随意关闭和断电。
    和celery的配置  task_reject_on_worker_lost = True task_acks_late = True后，处理逻辑几乎不约而同相似。
    """
    BROKER_KIND = 9

    def _shedual_task(self):
        while True:
            result = self.redis_db_frame.blpop(self._queue_name, timeout=60)
            # task_bytes = self.redis_db_frame.lpop(self._queue_name)
            if result:
                task_str = result[1].decode()
                # 如果运行了第20行，但没运行下面这一行，仍然有极小概率会丢失1个任务。但比不做控制随意关停，丢失几百个线程你的redis任务强多了。
                self._add_task_str_to_unack_zset(task_str, )
                self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：     {task_str}  ')
                task_dict = json.loads(task_str)
                kw = {'body': task_dict, 'task_str': task_str}
                self._submit_task(kw)

    def _requeue(self, kw):
        self.redis_db_frame.rpush(self._queue_name, json.dumps(kw['body']))


class RedisConsumerAckAble(ConsumerConfirmMixinWithTheHelpOfRedis, AbstractConsumer, ):
    """
    redis作为中间件实现的。将取出来的消息同时放入一个set中，代表unack消费状态。以支持对机器和python进程的随意关闭和断电。
    和celery的配置  task_reject_on_worker_lost = True task_acks_late = True后，处理逻辑几乎不约而同相似。

    lua_4 = '''
   local v = redis.call("lpop", KEYS[1])
   if v then
   redis.call('rpush',KEYS[2],v)
    end
   return v'''
    # script_4 = r.register_script(lua_4)
    #
    # print(script_4(keys=["text_pipelien1","text_pipelien1b"]))
    """
    BROKER_KIND = 9

    def _shedual_task(self):
        lua = '''
                     local v = redis.call("lpop", KEYS[1])
                     if v then
                     redis.call('zadd',KEYS[2],ARGV[1],v)
                      end
                     return v'''
        script = self.redis_db_frame.register_script(lua)
        while True:
            return_v = script(keys=[self._queue_name, self._unack_zset_name], args=[time.time()])
            if return_v:
                task_str = return_v.decode()
                self._add_task_str_to_unack_zset(task_str, )
                self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：     {task_str}  ')
                task_dict = json.loads(task_str)
                kw = {'body': task_dict, 'task_str': task_str}
                self._submit_task(kw)
            else:
                # print('xiuxi')
                time.sleep(0.1)

    def _requeue(self, kw):
        self.redis_db_frame.rpush(self._queue_name, json.dumps(kw['body']))
