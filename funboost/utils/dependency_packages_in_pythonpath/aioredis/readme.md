
## 1 asioredis包将不再更新 ，ptyhon 3.11 版本 import aioredis会出错。

相关问题：  https://github.com/aio-libs/aioredis-py/issues/1443


## 2 aioredis.exceptions.py的TimeoutError在python3.11有问题

### 2.1 现在错误的

class TimeoutError(asyncio.TimeoutError, builtins.TimeoutError, RedisError):
    pass

### 2.2 适配python 3.11版本

class TimeoutError(asyncio.TimeoutError, RedisError):
    pass


主要是修改了这里，由于一导入就报错，不方便打猴子补丁来替换，所以funboost整体不再使用aioredis包，而是导入这里的代码。