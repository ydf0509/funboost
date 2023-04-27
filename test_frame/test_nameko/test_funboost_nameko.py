from nameko.containers import ServiceContainer
from nameko.rpc import rpc

from funboost import register_custom_broker, boost, funboost_config_deafult
from funboost.consumers.nameko_consumer import NamekoConsumer
from funboost.publishers.nameko_publisher import NamekoPublisher

register_custom_broker(40,NamekoPublisher,NamekoConsumer)


@boost('test_nameko_queue',broker_kind=40,schedule_tasks_on_main_thread=True)
def f(a,b):
    print(a,b)



class MyService():
    name = 'funboost_nameko_service'

    @rpc
    def call(this, *args, **kwargs):
        print(args, kwargs)


url = f'amqp://{funboost_config_deafult.RABBITMQ_USER}:{funboost_config_deafult.RABBITMQ_PASS}@{funboost_config_deafult.RABBITMQ_HOST}:{funboost_config_deafult.RABBITMQ_PORT}/{funboost_config_deafult.RABBITMQ_VIRTUAL_HOST}'

nameko_config = {'AMQP_URI': url}
container = ServiceContainer(MyService, config=nameko_config)



if __name__ == '__main__':
    # f.consume()
    # print('565657')
    # f.push(1,2)

    container.start()
    container.wait()
