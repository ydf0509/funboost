from nameko.standalone.rpc import ClusterRpcProxy

from funboost.funboost_config_deafult import BrokerConnConfig

url = f'amqp://{BrokerConnConfig.RABBITMQ_USER}:{BrokerConnConfig.RABBITMQ_PASS}@{BrokerConnConfig.RABBITMQ_HOST}:{BrokerConnConfig.RABBITMQ_PORT}/{BrokerConnConfig.RABBITMQ_VIRTUAL_HOST}'

CONFIG = {'AMQP_URI': url}


def compute():
    with ClusterRpcProxy(CONFIG) as rpc:
        r = rpc.hello_service2.hello(1,2)
        print(r)




if __name__ == '__main__':
    compute()
