
print('导入nb_log之前的print是普通的')
import time
import sys
print(sys.path)

from nb_log import get_logger

# logger = get_logger('lalala',log_filename='jinzhifengzhuang.log',formatter_template=5)

# logger.debug(f'debug是绿色，说明是调试的，代码ok ')
# logger.info('info是天蓝色，日志正常 ')
# logger.warning('黄色yello，有警告了 ')
# logger.error('粉红色说明代码有错误 ')
# logger.critical('血红色，说明发生了严重错误 ')

# print('导入nb_log之后的print是强化版的可点击跳转的')



#raise  Exception("dsadsd")

while 1:
    time.sleep(5)