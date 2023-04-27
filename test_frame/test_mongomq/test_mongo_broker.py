from auto_run_on_remote import run_current_script_on_remote
run_current_script_on_remote()

import time
from multiprocessing import Process
from funboost import boost,BrokerEnum,FunctionResultStatusPersistanceConfig

@boost('test_mongo6',broker_kind=BrokerEnum.MONGOMQ,function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(True,True),qps=2)
def add(a,b):
    time.sleep(1)
    return a+b

add.push(100,200)

def multi_consume():
    for j in range(1000,2000):
        add.push(j,j*2)
    add.consume()
    time.sleep(100000000)

if __name__ == '__main__':
    for k in range(2000, 3000):
        add.push(k, k * 2)

    add.consume()
    add.multi_process_consume(3)
    ps = []
    for i in range(2):
        p = Process(target=multi_consume)
        p.start()
        ps.append(p)
    # for p in ps:
    #     p.join()
    time.sleep(1000*1000*10)
