import copy
import re

from function_scheduling_distributed_framework import frame_config
from function_scheduling_distributed_framework.consumers.base_consumer import ExceptionForRequeue, ExceptionForRetry, AbstractConsumer, ConsumersManager, FunctionResultStatusPersistanceConfig
from function_scheduling_distributed_framework.publishers.base_publisher import PriorityConsumingControlConfig
from function_scheduling_distributed_framework.factories.publisher_factotry import get_publisher
from function_scheduling_distributed_framework.factories.consumer_factory import get_consumer
from function_scheduling_distributed_framework.utils import nb_print, patch_print, LogManager


# noinspection PyPep8Naming
def patch_frame_config(MONGO_CONNECT_URL: str = None,

                       RABBITMQ_USER: str = None,
                       RABBITMQ_PASS: str = None, RABBITMQ_HOST: str = None,
                       RABBITMQ_PORT: int = None, RABBITMQ_VIRTUAL_HOST: str = None,

                       REDIS_HOST: str = None, REDIS_PASSWORD: str = None, REDIS_PORT: int = None, REDIS_DB: int = None,

                       NSQD_TCP_ADDRESSES: list = None,
                       NSQD_HTTP_CLIENT_HOST: str = None,
                       NSQD_HTTP_CLIENT_PORT: int = None,
                       KAFKA_BOOTSTRAP_SERVERS: list = None,

                       SQLACHEMY_ENGINE_URL='sqlite:////sqlachemy_queues/queues.db'

                       ):
    """
    对框架的配置使用猴子补丁的方式进行更改。利用了模块天然是单利的特性。格式参考frame_config.py
    :return:
    """
    kw = copy.copy(locals())
    for var_name, var_value in kw.items():
        if var_value is not None:
            setattr(frame_config, var_name, var_value)


def show_frame_config():
    nb_print('显示当前的项目中间件配置参数')
    for var_name in dir(frame_config):
        if var_name.isupper():
            var_value = getattr(frame_config, var_name)
            if var_name == 'MONGO_CONNECT_URL':
                if re.match('mongodb://.*?:.*?@.*?/.*', var_value):
                    mongo_pass = re.search('mongodb://.*?:(.*?)@', var_value).group(1)
                    mongo_pass_encryption = f'{"*" * (len(mongo_pass) - 2)}{mongo_pass[-1]}' if len(mongo_pass) > 3 else mongo_pass
                    var_value_encryption = re.sub(r':(\w+)@', f':{mongo_pass_encryption}@', var_value)
                    nb_print(f'{var_name}:             {var_value_encryption}')
                    continue
            if 'PASS' in var_name and len(var_value) > 3:  # 对密码打*
                nb_print(f'{var_name}:                {var_value[0]}{"*" * (len(var_value) - 2)}{var_value[-1]}')
            else:
                nb_print(f'{var_name}:                {var_value}')
