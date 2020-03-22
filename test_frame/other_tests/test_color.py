# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2020/1/13 0013 9:15
print('测试没有没有导入框架之前，print应该是白颜色,并且在控制台不知道是从哪个文件哪一行print出来的')

# 只要任意地方导入一次框架后，项目任意模块里面的print自动发生变化，只要是在此后发生的print一律变色＆可跳转。print变色和日志变色是独立的,可以按需选择。
from function_scheduling_distributed_framework import LogManager

print('导入utils_ydf后,自动打了print猴子补丁，此行颜色i你该发生变化，和pycharm下可点击跳转')

logger = LogManager('lalala').get_logger_and_add_handlers()

for i in range(3):
    logger.debug(f'在console里面设置为monokai主题下测试颜色{i}')
    logger.info(f'在console里面设置为monokai主题下测试颜色{i}')
    logger.warning(f'在console里面设置为monokai主题下测试颜色{i}')
    logger.error(f'在console里面设置为monokai主题下测试颜色{i}')
    logger.critical(f'在console里面设置为monokai主题下测试颜色{i}')
    print(f'直接print也会变色和可自动跳转，因为打了猴子补丁{i}')
