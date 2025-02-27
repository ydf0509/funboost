from test_persist import f,f2,time

for i in range(0, 1000000):
    f.push(i)
    f2.push(i)
    time.sleep(0.01)



