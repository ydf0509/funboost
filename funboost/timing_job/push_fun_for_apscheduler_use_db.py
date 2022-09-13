import importlib

def push_for_apscheduler_use_db(task_fun_file: str, task_fun_name, *args, **kwargs):
    """
    :param task_fun_file:   被boost装饰的函数的所在的文件路径，文件路径是相对于当前项目根目录，不是从磁盘根目录下的全路径。
                            例如你的项目是 myproj,里面有个 a/b/c.py，c.py文件里面有任务函数，那这里入参就写 'a/b/c.py'
                            也可以写成  'a.b.c'   ,两种方式都可以。
    :param task_fun_name: 函数名字
    :param args: 消费函数本身的入参
    :param kwargs: 消费函数本身的入参
    :return:
    """

    task_fun_file_for_import = task_fun_file.replace('/', '.').replace('.py', '')
    # print(task_fun_file_for_import,args,kwargs)
    task_fun = getattr(importlib.import_module(task_fun_file_for_import), task_fun_name)
    # task_fun(*args,**kwargs)
    # print(task_fun)
    task_fun.push(*args, **kwargs)



