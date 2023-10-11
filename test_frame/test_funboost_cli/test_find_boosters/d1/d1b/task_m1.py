from funboost import boost


@boost('test_find_queue1', )
def f(x, y):
    # time.sleep(100)
    print(f'{x} + {y} = {x + y}')
    return x + y


