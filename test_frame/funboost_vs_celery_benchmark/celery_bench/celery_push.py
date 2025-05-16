


from celery_consume import print_number
import nb_log
import datetime

if __name__ == '__main__':
    print(f'当前时间: {datetime.datetime.now()}')

    for i in range(100000):
        if i % 1000 == 0:
            print(f'当前时间: {datetime.datetime.now()} {i}')
        print_number.delay(i)
    print(f'当前时间: {datetime.datetime.now()}')


'''

在win11 + python3.9 + celery 5 + redis 中间件 + amd r7 5800h cpu 环境下测试

celery发布性能测试结果如下：

celery 发布10万条简单消息，耗时110秒，平均每秒能发布900条，从打印的发布时间间隔也能看出来，每隔1.1秒打印一次发布1000条
'''