import time

from funboost import boost, BrokerEnum, TaskOptions


@boost(queue_name="test", broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM)
def test(task):
    print(task["text"])

test.clear()
test.publish(msg={"task": {"text": 1}}, task_options=TaskOptions(countdown=0))
test.publish(msg={"task": {"text": 2}}, task_options=TaskOptions(countdown=1))
test.publish(msg={"task": {"text": 3}}, task_options=TaskOptions(countdown=60))
test.publish(msg={"task": {"text": 4}}, task_options=TaskOptions(countdown=5))
test.publish(msg={"task": {"text": 5}}, task_options=TaskOptions(countdown=1))


test.consume()
while True:
    time.sleep(60)
