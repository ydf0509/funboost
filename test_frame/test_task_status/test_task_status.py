import time
from funboost import boost,FunctionResultStatusPersistanceConfig

@boost('test_save_stuaus_queue',
       function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(is_save_status=True,is_save_result=True))
def add(a,b):
    time.sleep(1)
    raise Exception('出错')
    print('a +b :', a+b)
    return a+b

if __name__ == '__main__':
    add.push(1,2)
    add.consume()