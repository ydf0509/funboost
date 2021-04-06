# import gevent.monkey;gevent.monkey.patch_all()
import time

from function_scheduling_distributed_framework import task_deco, BrokerEnum,run_consumer_with_multi_process,ConcurrentModeEnum
import urllib3
import requests
http = urllib3.PoolManager()




@task_deco('speed_baidu', broker_kind=BrokerEnum.REDIS,
           log_level=20, concurrent_num=60,concurrent_mode=ConcurrentModeEnum.THREADING,
           is_using_distributed_frequency_control=True,is_print_detail_exception=False)
def baidu_speed(x,):
    # print(x)
    try:
        resp = requests.request('get','http://www.baidu.com/content-search.xml')
    except:
        pass




if __name__ == '__main__':

    run_consumer_with_multi_process(baidu_speed,10)
    # # f_test_speed2.consume()
