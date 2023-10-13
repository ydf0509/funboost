from funboost import boost


@boost('test_find_queue2', )
def f2(x, y):
    # time.sleep(100)
    print(f'{x} + {y} = {x + y}')
    return x + y


