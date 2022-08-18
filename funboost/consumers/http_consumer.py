# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:32
import asyncio
import json

from aiohttp import web
from aiohttp.web_request import Request

from funboost.consumers.base_consumer import AbstractConsumer


class HTTPConsumer(AbstractConsumer, ):
    """
    http 实现消息队列，不支持持久化，但不需要安装软件。
    """
    BROKER_KIND = 23

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        try:
            self._ip, self._port = self.queue_name.split(':')
            self._port = int(self._port)
        except Exception as e:
            self.logger.critical(f'http作为消息队列时候,队列名字必须设置为 例如 192.168.1.101:8200  这种,  ip:port')
            raise e

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

        routes = web.RouteTableDef()

        # noinspection PyUnusedLocal
        @routes.get('/')
        async def hello(request):
            return web.Response(text="Hello, from funboost")

        @routes.post('/queue')
        async def recv_msg(request: Request):
            data = await request.post()
            msg = data['msg']
            kw = {'body': json.loads(msg)}
            self._submit_task(kw)
            return web.Response(text="finish")

        app = web.Application()
        app.add_routes(routes)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        web.run_app(app, host='0.0.0.0', port=self._port, )

    def _confirm_consume(self, kw):
        pass  # 没有确认消费的功能。

    def _requeue(self, kw):
        pass
