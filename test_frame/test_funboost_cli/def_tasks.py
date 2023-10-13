from funboost import boost


@boost('test_cli1_queue', )
def f(x, y):
    # time.sleep(100)
    print(f'{x} + {y} = {x + y}')
    return x + y


@boost('test_cli2_queue', )
def f2(x, y):
    # time.sleep(100)
    print(f'{x} - {y} = {x - y}')
    return x - y
