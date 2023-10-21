import time

import eventlet

from funboost.funboost_config_deafult import BrokerConnConfig

eventlet.monkey_patch()
import nb_log
from nameko.containers import ServiceContainer
from nameko.rpc import rpc

url = f'amqp://{BrokerConnConfig.RABBITMQ_USER}:{BrokerConnConfig.RABBITMQ_PASS}@{BrokerConnConfig.RABBITMQ_HOST}:{BrokerConnConfig.RABBITMQ_PORT}/{BrokerConnConfig.RABBITMQ_VIRTUAL_HOST}'

CONFIG = {'AMQP_URI': url}

class HelloService:
    name = "hello_service2"

    @rpc
    def hello(self,a,b):

        print(f"a {a}  b: {b}  start")
        time.sleep(30)
        print(f"a {a}  b: {b}  over")
        return a + b


if __name__ == '__main__':
    '''
    nameko run nameko_server --broker amqp://admin:admin@192.168.64.151
    '''
    # from nameko.cli.run import run
    #
    # run([HelloService],  {'AMQP_URI': 'amqp://admin:admin@192.168.64.151'}, backdoor_port=None)



    container = ServiceContainer(HelloService, config={'AMQP_URI': url})

    container.start()
    container.wait()
    # try:
    #     container.wait()
    # except KeyboardInterrupt:
    #     container.kill()
    # container.stop()