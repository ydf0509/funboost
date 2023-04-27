from auto_run_on_remote import run_current_script_on_remote
run_current_script_on_remote()

from multiprocessing import Process
import pymongo

mongo_url = 'mongodb://admin:123456@192.168.70.128:27017/admin'

c = pymongo.MongoClient(mongo_url, connect=False) # 即使为false，如果在主进程中操作了 collection，那么fork也会报错不安全。

col = c.get_database('db3').get_collection('clo1')
col.insert_one({'a':4})

def f():
    col.insert_one({'a':1})


if __name__ == '__main__':
    for i in range(4):
        Process(target=f).start()