

from funboost_consume import print_number
import datetime

if __name__ == '__main__':
    for i in range(500000):
        if i % 1000 == 0:
            print(f'当前时间: {datetime.datetime.now()} {i}')
        print_number.push(i)


'''
在win11 + python3.9 + funboost + redis 中间件 + amd r7 5800h cpu 环境下测试 

funboost发布性能测试结果如下：

funboost 发布10万条消息，耗时5秒，平均每秒能发布20000条，从打印的发布时间间隔也能看出来,每隔0.05秒打印一次发布1000条
'''
