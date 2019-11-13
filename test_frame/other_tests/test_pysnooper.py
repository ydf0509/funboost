# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/11/6 0006 16:49

'''
测试改版的pysnooper装饰器。
'''
import requests
from function_scheduling_distributed_framework.utils import RedisMixin, pysnooper_ydf,LogManager

from test_frame.my_patch_frame_config import do_patch_frame_config

do_patch_frame_config()


def foo():
    raise TypeError('bad')


def bar():
    try:
        foo()
    except Exception:
        str(1)
        raise

logger = LogManager('test_pysnoop').get_logger_and_add_handlers(log_filename='test_pysnoop.log')

@pysnooper_ydf.snoop(depth=300)
def main():
    try:
        logger.info('测试pysnoop')
        for i in range(5):
            print(i)
        # resp = requests.get('http://www.baidu.com')
        # logger.debug(resp.text)
        # print(RedisMixin().redis_db_frame.keys())
        # bar()
    except:
        pass


expected_output = '''
Source path:... Whatever
12:18:08.017782 call        17 def main():
12:18:08.018142 line        18     try:
12:18:08.018181 line        19         bar()
    12:18:08.018223 call         8 def bar():
    12:18:08.018260 line         9     try:
    12:18:08.018293 line        10         foo()
        12:18:08.018329 call         4 def foo():
        12:18:08.018364 line         5     raise TypeError('bad')
        12:18:08.018396 exception    5     raise TypeError('bad')
        TypeError: bad
        Call ended by exception
    12:18:08.018494 exception   10         foo()
    TypeError: bad
    12:26:33.942623 line        11     except Exception:
    12:26:33.942674 line        12         str(1)
    12:18:08.018655 line        13         raise
    Call ended by exception
12:18:08.018718 exception   19         bar()
TypeError: bad
12:18:08.018761 line        20     except:
12:18:08.018787 line        21         pass
12:18:08.018813 return      21         pass
Return value:.. None
'''
if __name__ == '__main__':
    main()
