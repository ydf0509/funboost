import time

from funboost import boost, BrokerEnum, PriorityConsumingControlConfig


@boost(queue_name="test", broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM)
def test(task):
    print(task["text"])

test.clear()
test.publish(msg={"task": {"text": 1}}, priority_control_config=PriorityConsumingControlConfig(countdown=0))
test.publish(msg={"task": {"text": 2}}, priority_control_config=PriorityConsumingControlConfig(countdown=1))
test.publish(msg={"task": {"text": 3}}, priority_control_config=PriorityConsumingControlConfig(countdown=60))
test.publish(msg={"task": {"text": 4}}, priority_control_config=PriorityConsumingControlConfig(countdown=5))
test.publish(msg={"task": {"text": 5}}, priority_control_config=PriorityConsumingControlConfig(countdown=1))


test.consume()
while True:
    time.sleep(60)
