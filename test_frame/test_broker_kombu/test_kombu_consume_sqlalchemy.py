import time
from funboost import BrokerEnum, boost,funboost_config_deafult

'''
默认自动创建表 kombu_message 和 kombu_queue, sqlalchemy版本要选对，测试 1.4.8 可以，2.0.15版本报错。 
所有队列的消息在一个表中kombu_message，queue_id字段做区分是何种队列。
'''
@boost('test_kombu_sqlalchemy_queue2', broker_kind=BrokerEnum.KOMBU, qps=0.1,
       broker_exclusive_config={
           'kombu_url': f'sqla+mysql+pymysql://{funboost_config_deafult.MYSQL_USER}:{funboost_config_deafult.MYSQL_PASSWORD}'
                        f'@{funboost_config_deafult.MYSQL_HOST}:{funboost_config_deafult.MYSQL_PORT}/{funboost_config_deafult.MYSQL_DATABASE}',
           'transport_options': {},
           'prefetch_count': 500})
def f2(x, y):
    print(f'start {x} {y} 。。。')
    time.sleep(60)
    print(f'{x} + {y} = {x + y}')
    print(f'over {x} {y}')


@boost('test_kombu_sqlalchemy_queue3', broker_kind=BrokerEnum.KOMBU, qps=0.1,
       broker_exclusive_config={
           'kombu_url': f'sqla+mysql+pymysql://{funboost_config_deafult.MYSQL_USER}:{funboost_config_deafult.MYSQL_PASSWORD}'
                        f'@{funboost_config_deafult.MYSQL_HOST}:{funboost_config_deafult.MYSQL_PORT}/{funboost_config_deafult.MYSQL_DATABASE}',
           'transport_options': {},
           'prefetch_count': 500})
def f3(x, y):
    print(f'start {x} {y} 。。。')
    time.sleep(60)
    print(f'{x} + {y} = {x + y}')
    print(f'over {x} {y}')


if __name__ == '__main__':
    for i in range(100):
        f2.push(i, i + 1)
        f3.push(i,i*2)
    f2.consume()
    f3.consume()
