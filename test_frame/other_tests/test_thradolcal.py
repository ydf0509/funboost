import functools
import threading

tl = threading.local()


# def f1(b):
#     tl.x=b
#     tl.y = b+2
#     # f2()
#     print(tl.__dict__)
#     t2 = threading.Thread(target=f2,args=(tl.__dict__,))
#     t2.start()
#
# def f2(tl_dict):
#     tl2 = threading.local()
#     tl2.__dict__.update(tl_dict)
#     print(tl2.x)
#
#
#
# threading.Thread(target=f1,args=(3,)).start()
# threading.Thread(target=f1,args=(4,)).start()
import nb_log

# @functools.lru_cache()
def import_ThreadCurrentTask():
    from funboost.core.current_task import ThreadCurrentTask
    return ThreadCurrentTask

def f():
    import_ThreadCurrentTask()


print()
for i in range(10000):
    f()

print()