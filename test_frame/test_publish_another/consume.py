


from funboost import BoosterParams

@BoosterParams(queue_name='proj1_queue')
def f(x):
    print(x)


if __name__ == '__main__':
    f.push(1)
    f.consume()
