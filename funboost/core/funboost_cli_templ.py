"""
funboost现在 新增 命令行启动消费 发布  和清空消息

用户不要亲自使用 funboost_cli_default.py
"""
import sys
from pathlib import Path

from funboost.core.discovery_boosters import BoosterDiscovery

project_root_path = Path(__file__).absolute()
print(f'project_root_path is : {project_root_path}')
sys.path.insert(1, str(project_root_path))  # 这个是为了方便命令行不用用户手动先 export PYTHONPATTH=项目根目录

##### $$$$$$$$$$$$
#  以上的sys.path代码需要放在最上面,先设置好pythonpath再导入funboost相关的模块
##### $$$$$$$$$$$$


from funboost.core.funboost_fire import funboost_fire

# 需要启动的函数,那么该模块或函数建议建议要被import到这来, 否则需要要在 --import_modules_str 中指定用户项目中有哪些模块包括了booster
'''
有三种方式,自动找到有@boost装饰器,注册booster

1. 用户亲自把要启动的消费函数所在模块或函数 手动 import 一下到此模块来
2. 用户在使用命令行时候 --import_modules_str 指定导入哪些模块路径,就能启动那些队列名来消费和发布了.
3. 用户使用BoosterDiscovery.auto_discovery_boosters  自动 import 指定文件夹下的 .py 文件来实现.
'''

# BoosterDiscovery(['用户的消费函数文件的目录1','用户的消费函数文件的目录2']).auto_discovery_boosters()
BoosterDiscovery([]).auto_discovery()

if __name__ == '__main__':
    funboost_fire()
