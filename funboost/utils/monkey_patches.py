

import collections.abc

setattr(collections,'MutableMapping',collections.abc.MutableMapping)





'''

Traceback (most recent call last):
  File "D:\codes\funboost\funboost\concurrent_pool\async_pool_executor0223.py", line 267, in <module>
    test_async_pool_executor()
  File "D:\codes\funboost\funboost\concurrent_pool\async_pool_executor0223.py", line 225, in test_async_pool_executor
    from funboost.concurrent_pool import CustomThreadPoolExecutor as ThreadPoolExecutor
  File "D:\codes\funboost\funboost\__init__.py", line 8, in <module>
    from funboost.set_frame_config import patch_frame_config, show_frame_config
  File "D:\codes\funboost\funboost\set_frame_config.py", line 167, in <module>
    use_config_form_funboost_config_module()
  File "D:\codes\funboost\funboost\set_frame_config.py", line 115, in use_config_form_funboost_config_module
    m = importlib.import_module('funboost_config')
  File "D:\ProgramData\Miniconda3\envs\py310\lib\importlib\__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
  File "D:\codes\funboost\funboost_config.py", line 8, in <module>
    from funboost import concurrent_pool
  File "D:\codes\funboost\funboost\concurrent_pool\__init__.py", line 14, in <module>
    from .custom_evenlet_pool_executor import CustomEventletPoolExecutor
  File "D:\codes\funboost\funboost\concurrent_pool\custom_evenlet_pool_executor.py", line 7, in <module>
    from eventlet import greenpool, monkey_patch, patcher, Timeout
  File "D:\ProgramData\Miniconda3\envs\py310\lib\site-packages\eventlet\__init__.py", line 17, in <module>
    from eventlet import convenience
  File "D:\ProgramData\Miniconda3\envs\py310\lib\site-packages\eventlet\convenience.py", line 7, in <module>
    from eventlet.green import socket
  File "D:\ProgramData\Miniconda3\envs\py310\lib\site-packages\eventlet\green\socket.py", line 21, in <module>
    from eventlet.support import greendns
  File "D:\ProgramData\Miniconda3\envs\py310\lib\site-packages\eventlet\support\greendns.py", line 79, in <module>
    setattr(dns, pkg, import_patched('dns.' + pkg))
  File "D:\ProgramData\Miniconda3\envs\py310\lib\site-packages\eventlet\support\greendns.py", line 61, in import_patched
    return patcher.import_patched(module_name, **modules)
  File "D:\ProgramData\Miniconda3\envs\py310\lib\site-packages\eventlet\patcher.py", line 132, in import_patched
    return inject(
  File "D:\ProgramData\Miniconda3\envs\py310\lib\site-packages\eventlet\patcher.py", line 109, in inject
    module = __import__(module_name, {}, {}, module_name.split('.')[:-1])
  File "D:\ProgramData\Miniconda3\envs\py310\lib\site-packages\dns\namedict.py", line 35, in <module>
    class NameDict(collections.MutableMapping):
AttributeError: module 'collections' has no attribute 'MutableMapping'
'''
