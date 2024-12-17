from funboost import BoostersManager,BrokerEnum,PublisherParams


def my_fun(aaa):
    publisher = BoostersManager.get_cross_project_publisher(PublisherParams(queue_name='proj1_queue', broker_kind=BrokerEnum.SQLITE_QUEUE))
    publisher.publish({'x': aaa})
    # publisher.push( aaa)


for i in range(12):
    my_fun(i)
