from test_kombu_consume_redis import f1


for i in range(200):
    f1.push(i,i+1)
