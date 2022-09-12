import importlib

def push_for_apscheduler_use_db(task_fun_file: str, task_fun_name, *args, **kwargs):
    task_fun_file_for_import = task_fun_file.replace('/', '.').replace('.py', '')
    # print(task_fun_file_for_import,args,kwargs)
    task_fun = getattr(importlib.import_module(task_fun_file_for_import), task_fun_name)
    # task_fun(*args,**kwargs)
    # print(task_fun)
    task_fun.push(*args, **kwargs)



