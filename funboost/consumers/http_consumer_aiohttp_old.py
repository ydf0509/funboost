# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import asyncio
import json

# from aiohttp import web
# from aiohttp.web_request import Request

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.function_result_status_saver import FunctionResultStatus
from funboost.core.lazy_impoter import AioHttpImporter
from funboost.core.serialization import Serialization


class AioFutureStatusResult:
    def __init__(self,call_type:str):
        self.execute_finish_event = asyncio.Event()
        self.staus_result_obj: FunctionResultStatus = None
        self.call_type  = call_type  # sync_call   or  publish

    def set_finish(self):
        self.execute_finish_event.set()

    async def wait_finish(self,rpc_timeout):
        return await self.execute_finish_event.wait()

    def set_staus_result_obj(self, staus_result_obj:FunctionResultStatus):
        self.staus_result_obj = staus_result_obj

    def get_staus_result_obj(self):
        return self.staus_result_obj

class HTTPConsumer(AbstractConsumer, ):
    """
    aiohttp 实现消息队列，不支持持久化，但不需要安装软件。
    """


    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        # try:
        #     self._ip, self._port = self.queue_name.split(':')
        #     self._port = int(self._port)
        # except BaseException as e:
        #     self.logger.critical(f'http作为消息队列时候,队列名字必须设置为 例如 192.168.1.101:8200  这种,  ip:port')
        #     raise e
        self._ip = self.consumer_params.broker_exclusive_config['host']
        self._port = self.consumer_params.broker_exclusive_config['port']
        if self._port is None:
            raise ValueError('please specify port')

    # noinspection DuplicatedCode
    def _dispatch_task(self):
        # flask_app = Flask(__name__)
        #
        # @flask_app.route('/queue', methods=['post'])
        # def recv_msg():
        #     msg = request.form['msg']
        #     kw = {'body': json.loads(msg)}
        #     self._submit_task(kw)
        #     return 'finish'
        #
        # flask_app.run('0.0.0.0', port=self._port,debug=False)

        routes = AioHttpImporter().web.RouteTableDef()

        # noinspection PyUnusedLocal
        @routes.get('/')
        async def hello(request):
            return AioHttpImporter().web.Response(text="Hello, from funboost")

        @routes.post('/queue')
        async def recv_msg(request: AioHttpImporter().Request):
            data = await request.post()
            msg = data['msg']
            call_type = data['call_type']
            kw = {'body': msg,'call_type': call_type,}
            if call_type == 'sync_call':
                aio_future_status_result = AioFutureStatusResult(call_type=call_type)
                kw['aio_future_status_result'] = aio_future_status_result
            self._submit_task(kw)
            if data['call_type'] == 'sync_call':
                await aio_future_status_result.wait_finish(self.consumer_params.rpc_timeout)
                return AioHttpImporter().web.Response(text=Serialization.to_json_str(
                    aio_future_status_result.get_staus_result_obj().get_status_dict(without_datetime_obj=True)))
            return AioHttpImporter().web.Response(text="finish")

        app = AioHttpImporter().web.Application()
        app.add_routes(routes)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        AioHttpImporter().web.run_app(app, host='0.0.0.0', port=self._port, )

    def _frame_custom_record_process_info_func(self,current_function_result_status: FunctionResultStatus,kw:dict):
        if  kw['call_type'] == "sync_call":
            aio_future_status_result: AioFutureStatusResult = kw['aio_future_status_result']
            aio_future_status_result.set_staus_result_obj(current_function_result_status)
            aio_future_status_result.set_finish()
            self.logger.info(f'aio_future_status_result.set_finish()')

    # async def _aio_frame_custom_record_process_info_func(self,current_function_result_status: FunctionResultStatus,kw:dict):
    #     self.logger.info(666666)
    #     if kw['call_type'] == "sync_call":
    #         aio_future_status_result: AioFutureStatusResult = kw['aio_future_status_result']
    #         aio_future_status_result.set_staus_result_obj(current_function_result_status)
    #         aio_future_status_result.set_finish()
    #         self.logger.info(f'aio_future_status_result.set_finish()')
    def _confirm_consume(self, kw):
        pass  # 没有确认消费的功能。

    def _requeue(self, kw):
        pass
