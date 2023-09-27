import time

t1 = time.time()
# import nb_log
print(time.time() -t1)



import gevent
print(time.time() -t1)




import funboost
print(time.time() -t1)

# 获取gevent模块的源文件路径
# gevent_path = inspect.getfile(gevent)
# print("gevent 模块路径:", gevent_path)
#
# # 获取gevent模块的导入源码
# gevent_source = inspect.getsource(gevent)
# print("gevent 模块导入源码:")
# print(gevent_source)


# import inspect
# import gevent
#
# # 查找导入gevent模块的具体位置
# source_lines, line_num = inspect.findsource(gevent)
# print("gevent 模块导入位置：")
# print("文件路径:", inspect.getfile(gevent))
# print("行号:", line_num)
# print("代码行内容:", source_lines[line_num - 1].strip())

import sys
# print(sys.modules)

