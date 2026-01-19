#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Funboost Web Manager 管理工具

统一入口，提供命令行接口和交互式菜单

使用方法:
    python manage.py                    # 交互式菜单
    python manage.py init               # 一键初始化
    python manage.py start              # 启动所有服务
    python manage.py stop               # 停止所有服务
    python manage.py db init            # 初始化数据库
    python manage.py user create        # 创建用户

更多帮助:
    python manage.py --help
    python manage.py <command> --help
"""

import sys
import os
import logging
import io
import warnings

# 确保项目根目录在 Python 路径中
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 禁用 nb_log 的详细输出（在导入任何模块之前设置）
os.environ['SHOW_NB_LOG_LOGO'] = 'False'
os.environ['SHOW_PYCHARM_COLOR_SETINGS'] = 'False'
os.environ['SHOW_IMPORT_NB_LOG_CONFIG_PATH'] = 'False'

# 设置日志级别 - 必须在导入任何模块之前设置
logging.basicConfig(level=logging.ERROR, format='')

# 禁用 SQLAlchemy 的警告
from sqlalchemy import exc as sa_exc
warnings.filterwarnings('ignore', category=sa_exc.SAWarning)

# 禁用各种日志 - 在导入之前就设置好
for logger_name in [
    'persistqueue',
    'persistqueue.serializers.pickle',
    'funboost.prompt',
    'funboost',
    'nb_log',
    'sqlalchemy',
    'sqlalchemy.engine',
    'sqlalchemy.pool',
]:
    logging.getLogger(logger_name).setLevel(logging.ERROR)
    logging.getLogger(logger_name).propagate = False

# 临时重定向 stdout 和 stderr，捕获 nb_log 的 print 输出
_original_stdout = sys.stdout
_original_stderr = sys.stderr
_temp_stdout = io.StringIO()
_temp_stderr = io.StringIO()

sys.stdout = _temp_stdout
sys.stderr = _temp_stderr

try:
    # 导入 CLI 主模块（这会触发所有的导入）
    from scripts.cli.main import main
finally:
    # 恢复 stdout 和 stderr
    sys.stdout = _original_stdout
    sys.stderr = _original_stderr

if __name__ == '__main__':
    main()
