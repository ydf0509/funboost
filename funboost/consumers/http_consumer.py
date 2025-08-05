# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import asyncio
import json

# from aiohttp import web
# from aiohttp.web_request import Request

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.lazy_impoter import AioHttpImporter


class HTTPConsumer(AbstractConsumer, ):
    """
    http 实现消息队列，不支持持久化，但不需要安装软件。
    """
    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'host': '127.0.0.1', 'port': None}

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
    def _shedual_task(self):
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
            kw = {'body': msg}
            self._submit_task(kw)
            return AioHttpImporter().web.Response(text="finish")

        app = AioHttpImporter().web.Application()
        app.add_routes(routes)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        AioHttpImporter().web.run_app(app, host='0.0.0.0', port=self._port, )

    def _confirm_consume(self, kw):
        pass  # 没有确认消费的功能。

    def _requeue(self, kw):
        pass
