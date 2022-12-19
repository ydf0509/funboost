# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 14:57
import sys
import time

from funboost import boost, BrokerEnum
from nb_http_client import HttpOperator, ObjectPool

http_pool = ObjectPool(object_type=HttpOperator, object_pool_size=100, object_init_kwargs=dict(host='www.baidu.com', port=80),
                       max_idle_seconds=30)


@boost('test_baidu', broker_kind=BrokerEnum.REDIS, log_level=20, is_print_detail_exception=False, concurrent_num=200,qps=1000,
       is_using_distributed_frequency_control=True)
def request_url(urlx,n):
    with http_pool.get() as conn:
        r1 = conn.request_and_getresponse('GET', urlx)
        sys.stdout.write(f'{n} {r1.text[:10]} {r1.status} {time.strftime("%H:%M:%S")} \n')


if __name__ == '__main__':
    request_url.clear()
    for i in range(10000):
        url = 'https://www.baidu.com/content-search.xml'
        # url = 'http://mini.eastday.com/assets/v1/js/search_word.js'
        request_url.push(url,i)

    request_url.multi_process_consume(2)
