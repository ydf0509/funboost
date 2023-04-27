from nameko.standalone.rpc import ClusterRpcProxy

from funboost import funboost_config_deafult

url = f'amqp://{funboost_config_deafult.RABBITMQ_USER}:{funboost_config_deafult.RABBITMQ_PASS}@{funboost_config_deafult.RABBITMQ_HOST}:{funboost_config_deafult.RABBITMQ_PORT}/{funboost_config_deafult.RABBITMQ_VIRTUAL_HOST}'

CONFIG = {'AMQP_URI': url}


def compute():
    with ClusterRpcProxy(CONFIG) as rpc:
        r = rpc.hello_service2.hello(1,2)
        print(r)




if __name__ == '__main__':
    compute()
