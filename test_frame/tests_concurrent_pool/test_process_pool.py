#
# import os
# import threading
# from funboost.concurrent_pool.bounded_processpoolexcutor_gt_py37 import BoundedProcessPoolExecutor
#
# def test_f(x):
#     import time
#
#     print(x * 10, threading.get_ident(), os.getpid())
#     time.sleep(5)
#     # 1 / 0
#
#
# def start():
#     pool = BoundedProcessPoolExecutor(4)
#
#     for i in range(10):
#         print(i)
#         pool.submit(test_f, i)
#
# if __name__ == '__main__':
#     import nb_log
#     import time
#     from auto_run_on_remote import run_current_script_on_remote
#     # run_current_script_on_remote()
#     t = threading.Thread(target=start,)
#     t.start()
#     t.join()
#     # start()
#     # time.sleep(1000000)
#
#
#
#
# # #coding: utf-8
# # import multiprocessing
# # import time
# #
# # def func(msg):
# #     print ("msg:", msg)
# #     time.sleep(3)
# #     print ("end")
# #
# # if __name__ == "__main__":
# #     pool = multiprocessing.Pool(processes = 3)
# #     for i in range(4):
# #         msg = "hello %d" %(i)
# #         pool.apply_async(func, (msg, ))   #维持执行的进程总数为processes，当一个进程执行完毕后会添加新的进程进去


#coding=utf-8
from multiprocessing import Manager, Pool,Queue
import time, random, os
def writer(q):
  print('writer启动%s,父进程为%s'%(os.getpid(),os.getppid()))
  l1 = ['a','b','c','d','e']
  for value in l1:
    q.put(value)
def reader(q):
  print('reader启动%s，父进程为%s'%(os.getpid(),os.getppid()))
  for i in range(q.qsize()):
    print('reader从Queue获取到消息：%s'%q.get(True))
if __name__ == "__main__":
  print('父进程%s启动．．．'%os.getpid())
  q = Manager().Queue() #使用Manager中的Queue来初始化
  # q = Queue(10)
  po = Pool()
  # 使用阻塞模式创建进程，这样就不需要在reader中使用死循环了，可以让writer完全执行完成后，再用reader去读取
  po.apply(writer, (q,))
  po.apply(reader, (q,))
  po.close()
  po.join()
  print('%s结束'%os.getpid())