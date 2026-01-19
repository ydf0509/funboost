# -*- coding: utf-8 -*-
"""
单独启动 Funboost Web Manager

用于调试或单独运行 Web 管理界面
"""

# 加载 .env 环境变量
from dotenv import load_dotenv

load_dotenv()


from funboost.funboost_web_manager.app import start_funboost_web_manager

from tasks import *  

if __name__ == "__main__":
    print("=" * 50)
    print("启动 Funboost Web Manager (Debug 模式)")
    print("访问地址: http://127.0.0.1:27018")
    print("代码修改后会自动重载")
    print("=" * 50)

    # Debug 模式启动，支持自动 reload
    start_funboost_web_manager(block=True, debug=True)
