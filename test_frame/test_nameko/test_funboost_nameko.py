import time

from nameko.containers import ServiceContainer
from nameko.rpc import rpc

from funboost import register_custom_broker, boost, funboost_config_deafult,ConcurrentModeEnum
from funboost.consumers.nameko_consumer import NamekoConsumer
from funboost.publishers.nameko_publisher import NamekoPublisher

register_custom_broker(40,NamekoPublisher,NamekoConsumer)


@boost('test_nameko_queue',broker_kind=40,schedule_tasks_on_main_thread=False,concurrent_mode=ConcurrentModeEnum.EVENTLET)
def f(msg):
    print(msg)
    time.sleep(10)
    return 'hi'


#
# class MyService4():
#     name = 'funboost_nameko_service4'
#
#     @rpc
#     def call4(this, *args, **kwargs):
#         print(args, kwargs)
#
#
# url = f'amqp://{funboost_config_deafult.RABBITMQ_USER}:{funboost_config_deafult.RABBITMQ_PASS}@{funboost_config_deafult.RABBITMQ_HOST}:{funboost_config_deafult.RABBITMQ_PORT}/{funboost_config_deafult.RABBITMQ_VIRTUAL_HOST}'
#




if __name__ == '__main__':
    from eventlet import monkey_patch
    monkey_patch()
    f.consume()
    print('565657')
    for i in range(100):
        f.push(i)
    # from eventlet import monkey_patch
    # monkey_patch()
    # nameko_config = {'AMQP_URI': url}
    # container = ServiceContainer(MyService4, config=nameko_config)
    #
    # container.start()
    # container.wait()
