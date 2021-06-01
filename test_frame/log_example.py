print('导入nb_log之前的print是普通的')

from nb_log import get_logger

print('导入nb_log之后的print是强化版的可点击跳转的')

logger = get_logger('lalala', log_filename='lalala.log')

for i in range(100):
    logger.debug(f'debug是绿色，说明是调试的，代码ok。 ' * 4)
    logger.info('info是天蓝色，日志正常。 ' * 4)
    logger.warning('黄色yello，有警告了。 ' * 4)
    logger.error('粉红色说明代码有错误。 ' * 4)
    logger.critical('血红色，说明发生了严重错误。 ' * 4)
    print('只要导入nb_log一次之后的项目任意文件的print是强化版的可点击跳转的，在输出控制台点击行号能自动打开文件跳转到精确行号。')
