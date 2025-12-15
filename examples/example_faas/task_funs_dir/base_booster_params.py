from funboost import  BoosterParams, BrokerEnum



class Project1BoosterParams(BoosterParams):
    project_name:str = 'test_project1'  # 核心配置，项目名，设置后，web接口就可以只关心某个项目下的队列，减少无关返回信息的干扰。
    broker_kind:str = BrokerEnum.REDIS
    is_send_consumer_hearbeat_to_redis : bool= True # 向redis发送心跳，这样才能从redis获取相关队列的运行信息。
    is_using_rpc_mode:bool = True # 必须设置这一个参数为True，才能支持rpc功能。
    booster_group : str = 'test_group1' # 方便按分组启动消费
    should_check_publish_func_params:bool = True # 发布消息时，是否检查消息内容是否正确，不正确的消息格式立刻从接口返回报错消息内容不正确。