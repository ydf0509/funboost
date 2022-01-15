# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:32
"""

这个是加强版的可确认消费的redis消费实现，所以比redis_conusmer实现复杂很多。
这个可以确保随意反复多次停止重启脚本，任务永不丢失
"""
import json
import time
from deprecated.sphinx import deprecated
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.consumers.confirm_mixin import ConsumerConfirmMixinWithTheHelpOfRedis, ConsumerConfirmMixinWithTheHelpOfRedisByHearbeat


@deprecated(version='1.0', reason="This class not used")
class RedisConsumerAckAble000(ConsumerConfirmMixinWithTheHelpOfRedis, AbstractConsumer, ):
    """
    随意重启代码会极小概率丢失1个任务。
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
                # self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：     {task_str}  ')
                self._print_message_get_from_broker('reids', task_str)
                task_dict = json.loads(task_str)
                kw = {'body': task_dict, 'task_str': task_str}
                self._submit_task(kw)

    def _requeue(self, kw):
        self.redis_db_frame.rpush(self._queue_name, json.dumps(kw['body']))


@deprecated(version='1.0', reason="This class not used")
class RedisConsumerAckAble111(ConsumerConfirmMixinWithTheHelpOfRedis, AbstractConsumer, ):
    """
    随意重启代码不会丢失任务，使用的是超时10分钟没有确认消费就认为是已经断开了，重新回到代消费队列。
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
                     return v
                '''
        script = self.redis_db_frame.register_script(lua)
        while True:
            return_v = script(keys=[self._queue_name, self._unack_zset_name], args=[time.time()])
            if return_v:
                task_str = return_v.decode()
                self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：     {task_str}  ')
                task_dict = json.loads(task_str)
                kw = {'body': task_dict, 'task_str': task_str}
                self._submit_task(kw)
            else:
                # print('xiuxi')
                time.sleep(0.1)

    def _requeue(self, kw):
        self.redis_db_frame.rpush(self._queue_name, json.dumps(kw['body']))


class RedisConsumerAckAble(ConsumerConfirmMixinWithTheHelpOfRedisByHearbeat, AbstractConsumer, ):
    """
    随意重启代码不会丢失任务，采用的是配合redis心跳，将心跳过期的未确认的队列，全部重回消费队列。这种不需要等待10分钟，判断更精确。
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

    def _shedual_task000(self):
        # 可以采用lua脚本，也可以采用redis的watch配合pipeline使用。比代码分两行pop和zadd比还能减少一次io交互，还能防止丢失小概率一个任务。
        lua = '''
                     local v = redis.call("lpop", KEYS[1])
                     if v then
                     redis.call('zadd',KEYS[2],ARGV[1],v)
                      end
                     return v 
                '''
        script = self.redis_db_frame.register_script(lua)
        while True:
            return_v = script(keys=[self._queue_name, self._unack_zset_name], args=[time.time()])
            if return_v:
                task_str = return_v.decode()
                self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：     {task_str}  ')
                task_dict = json.loads(task_str)
                kw = {'body': task_dict, 'task_str': task_str}
                self._submit_task(kw)
            else:
                # print('xiuxi')
                time.sleep(0.5)

    def _shedual_task(self):
        lua = '''
                     local task_list = redis.call("lrange", KEYS[1],0,99)
                     redis.call("ltrim", KEYS[1],100,-1)
                     if (#task_list > 0) then
                        for task_index,task_value in ipairs(task_list)
                        do
                            redis.call('zadd',KEYS[2],ARGV[1],task_value)
                        end
                        return task_list
                    else
                        --local v = redis.call("blpop",KEYS[1],4)      
                        --return v
                      end

                '''
        """
        local v = redis.call("blpop",KEYS[1],60)  # redis 的lua 脚本禁止使用blpop
        local v = redis.call("lpop",KEYS[1])
        """
        script = self.redis_db_frame_version3.register_script(lua)
        while True:
            task_str_list = script(keys=[self._queue_name, self._unack_zset_name], args=[time.time()])
            if task_str_list:
                self._print_message_get_from_broker('redis', task_str_list)
                # self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：  {task_str_list}  ')
                for task_str in task_str_list:
                    task_dict = json.loads(task_str)
                    kw = {'body': task_dict, 'task_str': task_str}
                    self._submit_task(kw)
            else:
                time.sleep(0.5)

    def _requeue(self, kw):
        self.redis_db_frame.rpush(self._queue_name, json.dumps(kw['body']))
