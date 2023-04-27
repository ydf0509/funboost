
# from test_funboost_nameko import f
# f.push(1,2)
from nameko.standalone.rpc import ClusterRpcProxy

from funboost import funboost_config_deafult

url = f'amqp://{funboost_config_deafult.RABBITMQ_USER}:{funboost_config_deafult.RABBITMQ_PASS}@{funboost_config_deafult.RABBITMQ_HOST}:{funboost_config_deafult.RABBITMQ_PORT}/{funboost_config_deafult.RABBITMQ_VIRTUAL_HOST}'





nameko_config = {'AMQP_URI': url}

with ClusterRpcProxy(nameko_config) as rpc:

    res = rpc.funboost_nameko_service4.call4(1,2)