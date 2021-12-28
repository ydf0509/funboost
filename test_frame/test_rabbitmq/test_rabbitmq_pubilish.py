from test_frame.test_rabbitmq.test_rabbitmq_consume import test_fun

test_fun.clear()
for i in range(20):
    test_fun.push(i)

