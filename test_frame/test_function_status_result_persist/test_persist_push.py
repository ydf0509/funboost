from test_persist import my_consuming_function,f2,time,aio_f3

for i in range(0, 10000):
    my_consuming_function.push(i)
    f2.push(i,i*2)
    aio_f3.push(i)
    time.sleep(0.01)



