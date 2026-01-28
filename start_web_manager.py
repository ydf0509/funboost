# -*- coding: utf-8 -*-
"""
单独启动 Funboost Web Manager

用于调试或单独运行 Web 管理界面
"""

# 加载 .env 环境变量
from dotenv import load_dotenv

load_dotenv()


from funboost.funboost_web_manager.app import start_funboost_web_manager
from funboost.core.cli.discovery_boosters import BoosterDiscovery
import os

# 自动发现并注册 tasks 目录下的 @boost 函数
project_root = os.path.dirname(os.path.abspath(__file__))
BoosterDiscovery(
    project_root_path=project_root,
    booster_dirs=['tasks'],
    max_depth=1,
    py_file_re_str='process'  # 只扫描包含 'process' 的文件
).auto_discovery()


if __name__ == "__main__":

    start_funboost_web_manager(block=True, debug=True)
