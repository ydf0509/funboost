from test_broker_dramatiq import f1,f2

for i in range(1000,3000):
    f1.push(i)
    f2.push(i*2)