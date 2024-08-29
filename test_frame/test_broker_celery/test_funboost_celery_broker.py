import time
import celery.result
import requests

from funboost import boost, BrokerEnum
from funboost.assist.celery_helper import CeleryHelper
import kombu

@boost('tets_queue31a5', broker_kind=BrokerEnum.CELERY, concurrent_num=10,is_print_detail_exception=False,)
def fa(x, y):
    time.sleep(3)
    print(6666, x, y)
    # requests.get('123')
    # 1/0
    return x + y


@boost('tets_funboost_celery_queue31b', broker_kind=BrokerEnum.CELERY, concurrent_num=10,
       broker_exclusive_config={'celery_app_config':
                                    {'task_default_rate_limit': '2/s', }}
       )
def fb(a, b):
    time.sleep(2)
    print(7777, a, b)
    return a - b


if __name__ == '__main__':
    fa.consume()
    fb.consume()

    for i in range(10):
        r = fa.push(i, i + 1)  # type: celery.result.AsyncResult
        # print(type(r), r)
        # print(r.get())
        fb.delay(i, i * 2)

    CeleryHelper.realy_start_celery_worker()

'''

linux celery 报错EntryPoints‘ object has no attribute ‘get‘ ，这么做
https://blog.csdn.net/weixin_73672704/article/details/129477312

pip install frozenlist==1.3.1 geopy==2.2.0 humanize==4.3.0 idna==3.3 importlib-metadata==4.12.0 jsonschema==4.9.0 korean_lunar_calendar==0.2.1 marshmallow==3.17.0 pyOpenSSL==22.0.0 pyrsistent==0.18.1 python-dotenv==0.20.0 pytz==2022.2.1 selenium==4.4.0 simplejson==3.17.6 sniffio==1.2.0 trio==0.21.0 urllib3==1.26.11 wsproto==1.1.0 zipp==3.8.1
 
# 如果上述安装仍未解决, 则执行以下安装(笔者执行完上述安装即能解决问题)
pip install backoff==2.1.2 colorama==0.4.5 croniter==1.3.5 cryptography==37.0.4 email-validator==1.2.1 flask-compress==1.12 flask-migrate==3.1.0 aiohttp==3.8.1 aiosignal==1.2.0 Mako==1.2.1 Babel==2.10.3

'''
