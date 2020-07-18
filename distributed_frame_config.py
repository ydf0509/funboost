# -*- coding: utf-8 -*-
"""
1.1） 此py配置文件的内容是可以不拘于形式的，例如在此文件里面可以根据环境写if else 判断，或者写其他python代码，里面写各种函数和变量都可以的。但模块必须按需包括以下名字的变量，
例如 如果不使用rabbitmq作为中间件，只使用redis做中间件，则此模块可以没有RABBITMQ_USER RABBITMQ_PASS MOOGO KAFKA sql数据库等这些变量，只需要redis相关的变量就可以。

1.2）如果你的py启动脚本是项目的深层目录下，你也可以在那个启动目录下，放入这个文件，
框架会优先读取启动脚本所在目录的distributed_frame_config.py作为配置，
如果启动脚本所在目录下无distributed_frame_config.py文件，则会使用项目根目录下的distributed_frame_config.py做配置。

2）也可以使用 patch_frame_config函数进行配置的覆盖和指定。
用法为：

from function_scheduling_distributed_framework import patch_frame_config, show_frame_config
# 初次接触使用，可以不安装任何中间件，使用本地持久化队列。正式墙裂推荐安装rabbitmq。
# 使用打猴子补丁的方式修改框架配置。这里为了演示，列举了所有中间件的参数，
# 实际是只需要对使用到的中间件的配置进行赋值即可。
patch_frame_config(MONGO_CONNECT_URL='mongodb://myUserAdminxx:xxxx@xx.90.89.xx:27016/admin',

                   RABBITMQ_USER='silxxxx',
                   RABBITMQ_PASS='Fr3Mxxxxx',
                   RABBITMQ_HOST='1xx.90.89.xx',
                   RABBITMQ_PORT=5672,
                   RABBITMQ_VIRTUAL_HOST='test_host',

                   REDIS_HOST='1xx.90.89.xx',
                   REDIS_PASSWORD='yxxxxxxR',
                   REDIS_PORT=6543,
                   REDIS_DB=7,

                   NSQD_TCP_ADDRESSES=['xx.112.34.56:4150'],
                   NSQD_HTTP_CLIENT_HOST='12.34.56.78',
                   NSQD_HTTP_CLIENT_PORT=4151,

                   KAFKA_BOOTSTRAP_SERVERS=['12.34.56.78:9092'],
                   
                   SQLACHEMY_ENGINE_URL = 'mysql+pymysql://root:123456@127.0.0.1:3306/sqlachemy_queues?charset=utf8',
                   )

"""



# 以下为配置，请您按需修改。

MONGO_CONNECT_URL = 'mongodb://myUserAdmin:8mwTdy1klnSYepNo@' + '192.168.199.202' + ':27016/admin'

RABBITMQ_USER = 'silktest'
RABBITMQ_PASS = 'Fr3M3j@lXZLF*iMB'
RABBITMQ_HOST = '192.168.199.202'
RABBITMQ_PORT = 5672
RABBITMQ_VIRTUAL_HOST = 'test_host'

# 
# REDIS_HOST = '192.168.199.202'
# REDIS_PASSWORD = 'yMxsueZD9yx0AkfR'
# REDIS_PORT = 6543
# REDIS_DB = 7

REDIS_HOST = '127.0.0.1'
REDIS_PASSWORD = ''
REDIS_PORT = 6379
REDIS_DB = 7
# 
# NSQD_TCP_ADDRESSES = ['127.0.0.1:4150']
# NSQD_HTTP_CLIENT_HOST = '127.0.0.1'
# NSQD_HTTP_CLIENT_PORT = 4151
# 
# KAFKA_BOOTSTRAP_SERVERS = ['127.0.0.1:9092']
# 
# SQLACHEMY_ENGINE_URL ='sqlite:////sqlachemy_queues/queues.db'

# nb_log包的第几个日志模板，内置了7个模板，可以在你当前项目根目录下的nb_log_config.py文件扩展模板。
# NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER = 7               
