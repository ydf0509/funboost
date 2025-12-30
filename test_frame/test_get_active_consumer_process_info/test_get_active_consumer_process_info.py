from funboost import ActiveCousumerProcessInfoGetter

'''
获取分布式环境中的消费进程信息。
使用这里面的4个方法需要相应函数的@boost装饰器设置 is_send_consumer_heartbeat_to_redis=True，这样会自动发送活跃心跳到redis。否则查询不到该函数的消费者进程信息。
要想使用消费者进程信息统计功能，用户无论使用何种消息队列中间件类型，用户都必须安装redis，并在 funboost_config.py 中配置好redis链接信息
'''

#获取分布式环境中 test_queue 队列的所有消费者信息
print(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_queue_name('test_queue'))

#获取分布式环境中 当前列机器的所有消费者信息
print(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_ip())

#获取分布式环境中 指定ip的所有消费者信息
print(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_ip('10.0.195.220'))

#获取分布式环境中 所有 队列的所有消费者信息，按队列划分
print(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_queue_name())

#获取分布式环境中 所有 机器的所有消费者信息，按ip划分
print(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_ip())