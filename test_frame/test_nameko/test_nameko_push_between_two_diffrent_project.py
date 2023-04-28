from funboost import get_publisher, BrokerEnum
from funboost.assist.user_custom_broker_register import register_nameko_broker

register_nameko_broker()
publisher1 = get_publisher('test_nameko_queue', broker_kind=BrokerEnum.NAMEKO)
publisher2 = get_publisher('test_nameko_queue2', broker_kind=BrokerEnum.NAMEKO)

for i in range(100):
    print(publisher1.publish({'a':i,'b':i+1}))
    print(publisher2.publish({'x':i,'y':i+1}))
