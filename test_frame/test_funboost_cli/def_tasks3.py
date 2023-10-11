from funboost import boost


@boost('test_cli3_queue', )
def f3(x, y):
    # time.sleep(100)
    print(f'f3 {x} + {y} = {x + y}')
    return x + y


