import urllib3
import json
import nb_log
import decorator_libs

# https://www.cnblogs.com/YrRoom/p/14054282.html

"""
-p 18083 服务器启动端口
-p 1882 TCP端口
-p 8083 WS端口
-p 8084 WSS端口
-p 8883 SSL端口
"""

"""
非常适合 前端订阅唯一uuid的topic 然后表单中带上这个topic名字请求python接口 -> 接口中发布任务到rabbitmq或redis消息队列 ->
后台消费进程执行任务消费,并将结果发布到mqtt的那个唯一uuid的topic -> mqtt 把结果推送到前端。

使用ajax轮训或者后台导入websocket相关的包来做和前端的长耗时任务的交互都是伪命题，没有mqtt好。
"""


class MqttHttpHelper(nb_log.LoggerMixin, nb_log.LoggerLevelSetterMixin):

    def __init__(self, mqtt_publish_url='http://127.0.0.1:18083/api/v2/mqtt/publish', user='admin', passwd='public', display_full_msg=False):
        """
        :param mqtt_publish_url: mqtt的http接口，这是mqtt中间件自带的，不是重新自己实现的接口。不需要导入paho.mqtt.client,requeests urllib3即可。
        :param display_full_msg: 时候打印发布的任务
        """
        self._mqtt_publish_url = mqtt_publish_url
        self.http = urllib3.PoolManager()
        self._headers = urllib3.util.make_headers(basic_auth=f'{user}:{passwd}')
        self._headers['Content-Type'] = 'application/json'
        self._display_full_msg = display_full_msg

    # @decorator_libs.tomorrow_threads(10)
    def pub_message(self, topic, msg):
        msg = json.dumps(msg) if isinstance(msg, (dict, list)) else msg
        if not isinstance(msg, str):
            raise Exception('推送的不是字符串')
        post_data = {"qos": 1, "retain": False, "topic": topic, "payload": msg}
        try:  # UnicodeEncodeError: 'latin-1' codec can't encode character '\u6211' in position 145: Body ('我') is not valid Latin-1. Use body.encode('utf-8') if you want to send it encoded in UTF-8.
            resp_dict = json.loads(self.http.request('post', self._mqtt_publish_url, body=json.dumps(post_data),
                                                     headers=self._headers).data)
        except UnicodeEncodeError as e:
            self.logger.warning(e)
            post_data['payload'] = post_data['payload'].encode().decode('latin-1')
            resp_dict = json.loads(self.http.request('post', self._mqtt_publish_url, body=json.dumps(post_data),
                                                     headers=self._headers).data)
        if resp_dict['code'] == 0:
            self.logger.debug(f' 推送mqtt成功 ，主题名称是:{topic} ，长度是 {len(msg)}， 消息是 {msg if self._display_full_msg else msg[:200]} ')
        else:
            self.logger.debug(f' 推送mqtt失败,主题名称是:{topic},mqtt返回响应是 {json.dumps(resp_dict)} ， 消息是 {msg if self._display_full_msg else msg[:200]}')


if __name__ == '__main__':
    with decorator_libs.TimerContextManager():
        mp = MqttHttpHelper('http://192.168.6.130:18083/api/v2/mqtt/publish')
        for i in range(2000):
            mp.pub_message('/topic_test_uuid123456', 'msg_test3')
