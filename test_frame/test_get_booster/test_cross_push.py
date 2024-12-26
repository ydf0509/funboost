from funboost import BoostersManager, PublisherParams, BrokerEnum

pb = BoostersManager.get_cross_project_publisher(PublisherParams(queue_name='test_cross_qeueu1', broker_kind=BrokerEnum.REDIS, publish_msg_log_use_full_msg=True))
pb.publish({"a": 1, "b": 2})
