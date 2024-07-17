import asyncio
import json
import threading
import time

from funboost import EmptyConsumer
from funboost.assist.faststream_helper import broker,app,get_broker
from faststream import FastStream,Context
from faststream.annotations import Logger

from funboost.concurrent_pool.async_helper import simple_run_in_executor
from funboost.core.helper_funs import delete_keys_and_return_new_dict


class FastStreamConsumer(EmptyConsumer):
    def custom_init(self):
        self.broker = get_broker(max_consumers=self.consumer_params.concurrent_num)
        subc = self.broker.subscriber(self.queue_name)
        # @broker.subscriber(self.queue_name)
        async def f(msg:str, logger: Logger,message=Context(),broker=Context(),context=Context(),):
            self.logger.debug(f' 这条消息是 faststream 从 {self.queue_name} 队列中取出 ,是由 faststream 框架调度 {self.consuming_function.__name__} 函数处理,msg:{message} {context}')
            # print(logger.name)
            # return self.consuming_function(*args, **kwargs) # 如果没有声明 autoretry_for ，那么消费函数出错了就不会自动重试了。
            # print(msg)
            function_only_params = delete_keys_and_return_new_dict(json.loads(msg))
            if self._consuming_function_is_asyncio:
                result = await self.consuming_function(**function_only_params)
            else:
                result = await simple_run_in_executor(self.consuming_function,**function_only_params)
            # print(result)
            return result
        subc(f)
        self.faststream_subscriber = subc

    def _shedual_task(self):
        """ 完全由faststream框架接管控制消费，不使用funboost的AbstractConsumer的_run"""
        while 1:
            time.sleep(100)


    def _confirm_consume(self, kw):
        pass

    def start_consuming_message(self):
        def _f():
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.broker.connect())
            loop.run_until_complete(self.faststream_subscriber.start())
            loop.run_forever()
        self.keep_circulating(10, block=False)(_f)()
        # threading.Thread(target=_f).start()

    def _requeue(self, kw):
        pass