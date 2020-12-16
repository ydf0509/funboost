# -*- coding: utf-8 -*-
"""
此文件是分布式函数调度框架第一次运行时候自动生成的，按需修改里面的配置项。
比如你只用redis，把redis前面的 # 注释放开，修改成你的值，无需理会其他配置项如 rabbitmq  kafka。

1.1） 此py配置文件的内容是可以不拘于形式的，例如在此文件里面可以根据环境写if else 判断，或者写其他python代码，里面写各种函数和变量都可以的。但模块必须按需包括以下名字的变量，
例如 如果不使用rabbitmq作为中间件，只使用redis做中间件，则此模块可以没有RABBITMQ_USER RABBITMQ_PASS MOOGO KAFKA sql数据库等这些变量，只需要redis相关的变量就可以。

1.2）如果你的py启动脚本是项目的深层目录下，你也可以在那个启动目录下，放入这个文件，
框架会优先读取启动脚本所在目录的distributed_frame_config.py作为配置，
如果启动脚本所在目录下无 distributed_frame_config.py 文件，则会使用项目根目录下的distributed_frame_config.py做配置。

"""

# 以下为配置，请按需修改。

# MONGO_CONNECT_URL = f'mongodb://yourname:yourpassword@127.0.01:27017/admin'
# 
# RABBITMQ_USER = 'rabbitmq_user'
# RABBITMQ_PASS = 'rabbitmq_pass'
# RABBITMQ_HOST = '127.0.0.1'
# RABBITMQ_PORT = 5672
# RABBITMQ_VIRTUAL_HOST = 'rabbitmq_virtual_host'
# 
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

# SQLLITE_QUEUES_PATH = '/sqllite_queues'

# ROCKETMQ_NAMESRV_ADDR = '192.168.199.202:9876'

# nb_log包的第几个日志模板，内置了7个模板，可以在你当前项目根目录下的nb_log_config.py文件扩展模板。第5个模板可以点击跳转到框架内部，但有点占控制台面积，第7个模板简单不可点击跳转到框架内部。
# NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER = 7     
# FSDF_DEVELOP_LOG_LEVEL = 50   # 开发时候的日志，进攻自己用，所以日志级别跳到最高

# TIMEZONE = 'Asia/Shanghai'          
