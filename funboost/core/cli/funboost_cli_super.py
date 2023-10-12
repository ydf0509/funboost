"""
funboost现在 新增 命令行启动消费 发布  和清空消息

用户不要亲自使用 funboost_cli_default.py
"""
import sys
from pathlib import Path

import fire




from funboost.core.cli.funboost_fire import BoosterFire, check_pass_params

if __name__ == '__main__':
    check_pass_params()
    fire.Fire(BoosterFire,)
