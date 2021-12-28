# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 12:12
import json
from funboost.publishers.base_publisher import AbstractPublisher
import http.client
from urllib.parse import quote
from funboost import funboost_config_deafult
import urllib3

"""
http://blog.zyan.cc/httpsqs/
"""


class HttpsqsPublisher(AbstractPublisher):
    """
    使用httpsqs作为中间件
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        conn = http.client.HTTPConnection(host=funboost_config_deafult.HTTPSQS_HOST, port=funboost_config_deafult.HTTPSQS_PORT)
        url = f"/?name={self._queue_name}&opt=maxqueue&num=1000000000&auth={funboost_config_deafult.HTTPSQS_AUTH}&charset=utf-8"
        conn.request("GET", url)
        self.logger.info(conn.getresponse().read(1000))

        self.http = urllib3.PoolManager(20)

    def opt_httpsqs000(self, opt=None, data=''):
        data_url_encode = quote(data)
        resp = self.http.request('get', url=f'http://{funboost_config_deafult.HTTPSQS_HOST}:{funboost_config_deafult.HTTPSQS_PORT}' +
                                            f"/?name={self._queue_name}&opt={opt}&data={data_url_encode}&auth={funboost_config_deafult.HTTPSQS_AUTH}&charset=utf-8")
        return resp.data.decode()

    def opt_httpsqs(self, opt=None, data=''):
        conn = http.client.HTTPConnection(host=funboost_config_deafult.HTTPSQS_HOST, port=funboost_config_deafult.HTTPSQS_PORT)
        data_url_encode = quote(data)
        url = f"/?name={self._queue_name}&opt={opt}&data={data_url_encode}&auth={funboost_config_deafult.HTTPSQS_AUTH}&charset=utf-8"
        conn.request("GET", url)
        r = conn.getresponse()
        resp_text = r.read(1000000).decode()
        # print(url,r.status, resp_text)
        conn.close()
        return resp_text

    def concrete_realization_of_publish(self, msg):
        # curl "http://host:port/?name=your_queue_name&opt=put&data=经过URL编码的文本消息&auth=mypass123"
        text = self.opt_httpsqs('put', msg)
        if text != 'HTTPSQS_PUT_OK':
            self.logger.critical(text)

    def clear(self):
        # curl "http://host:port/?name=your_queue_name&opt=reset&auth=mypass123"
        # HTTPSQS_RESET_OK
        text = self.opt_httpsqs('reset')
        if text != 'HTTPSQS_RESET_OK':
            self.logger.critical(text)
        else:
            self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    def get_message_count(self):
        text = self.opt_httpsqs('status_json')
        status_dict = json.loads(text)
        # print(status_dict)
        return status_dict['putpos'] - status_dict['getpos']

    def close(self):
        self.http.clear()
