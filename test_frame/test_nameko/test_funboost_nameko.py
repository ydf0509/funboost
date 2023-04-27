from nameko.containers import ServiceContainer
from nameko.rpc import rpc

from funboost import register_custom_broker, boost, funboost_config_deafult
from funboost.consumers.nameko_consumer import NamekoConsumer
from funboost.publishers.nameko_publisher import NamekoPublisher

register_custom_broker(40,NamekoPublisher,NamekoConsumer)


# @boost('test_nameko_queue',broker_kind=40,schedule_tasks_on_main_thread=True)
# def f(a,b):
#     print(a,b)



class MyService4():
    name = 'funboost_nameko_service4'

    @rpc
    def call4(this, *args, **kwargs):
        print(args, kwargs)


url = f'amqp://{funboost_config_deafult.RABBITMQ_USER}:{funboost_config_deafult.RABBITMQ_PASS}@{funboost_config_deafult.RABBITMQ_HOST}:{funboost_config_deafult.RABBITMQ_PORT}/{funboost_config_deafult.RABBITMQ_VIRTUAL_HOST}'





if __name__ == '__main__':
    # f.consume()
    # print('565657')
    # f.push(1,2)
    from eventlet import monkey_patch
    monkey_patch()
    nameko_config = {'AMQP_URI': url}
    container = ServiceContainer(MyService4, config=nameko_config)

    container.start()
    container.wait()
