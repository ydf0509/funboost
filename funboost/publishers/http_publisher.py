# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import threading

from funboost.core.function_result_status_saver import FunctionResultStatus
from funboost.core.serialization import Serialization
from funboost.publishers.base_publisher import AbstractPublisher
from urllib3 import PoolManager


class HTTPPublisher(AbstractPublisher, ):
    """
    http实现的，不支持持久化。
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._http = PoolManager(maxsize=100)
        self._ip = self.publisher_params.broker_exclusive_config['host']
        self._port = self.publisher_params.broker_exclusive_config['port']
        self._ip_port_str = f'{self._ip}:{self._port}'
        if self._port is None:
            raise ValueError('please specify port')


    def _publish_impl(self, msg):
        url = self._ip_port_str + '/queue'
        self._http.request('post', url, fields={'msg': msg,'call_type':'publish'})

    def sync_call(self, msg_dict: dict, is_return_rpc_data_obj=True):
        url = self._ip_port_str + '/queue'
        response = self._http.request('post', url, 
                  fields={'msg': Serialization.to_json_str(msg_dict),'call_type':'sync_call'})
        json_resp =  response.data.decode('utf-8')
        # import requests
        # response = requests.request('post', url, 
        #           data={'msg': Serialization.to_json_str(msg_dict),'call_type':'sync_call'})
        # json_resp =  response.text()
        if is_return_rpc_data_obj:
            return FunctionResultStatus.parse_status_and_result_to_obj(Serialization.to_dict(json_resp))
        else:
            return Serialization.to_dict(json_resp)


    def clear(self):
        pass  # udp没有保存消息

    def get_message_count(self):
        return -1  # http模式没有持久化保存消息

    def close(self):
        pass
