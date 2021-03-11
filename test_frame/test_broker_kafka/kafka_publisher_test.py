from  test_frame.test_broker_kafka.kafka_cosumer_test import f


i = 203
f.push(i)


for i in range(200):
    f.push(i)