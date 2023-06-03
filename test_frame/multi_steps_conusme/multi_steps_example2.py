from funboost import boost


@boost('s1q',qps=0.2)
def step1(x):
    print(f'x 的值是 {x}')
    if x == 0:
        for i in range(1, 10):
            step1.publish(dict(x=x + i))
    for j in range(10):
        step2.publish(dict(y=x * 100 + j))

@boost('s2q',qps=2)
def step2(y):
    print(f'y 的值是 {y}')


if __name__ == '__main__':

    step1.push(0)
    step1.consume()
    step2.multi_process_consume(2)
    #
    # print(step1.consumer.consuming_function.__name__)

    step2(111)

