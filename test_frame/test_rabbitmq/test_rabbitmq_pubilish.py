from test_frame.test_rabbitmq.test_rabbitmq_consume import test_fun,test_fun2

test_fun.clear()
for i in range(200000):
    test_fun.push(i)
    test_fun2.push(i)


