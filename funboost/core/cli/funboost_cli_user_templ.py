"""
funboost现在 新增 命令行启动消费 发布  和清空消息


"""
import sys
from pathlib import Path
import fire

project_root_path = Path(__file__).absolute().parent
print(f'project_root_path is : {project_root_path}  ,请确认是否正确')
sys.path.insert(1, str(project_root_path))  # 这个是为了方便命令行不用用户手动先 export PYTHONPATTH=项目根目录

# $$$$$$$$$$$$
# 以上的sys.path代码需要放在最上面,先设置好pythonpath再导入funboost相关的模块
# $$$$$$$$$$$$


from funboost.core.cli.funboost_fire import BoosterFire, env_dict
from funboost.core.cli.discovery_boosters import BoosterDiscovery

# 需要启动的函数,那么该模块或函数建议建议要被import到这来, 否则需要要在 --import_modules_str 或 booster_dirs 中指定用户项目中有哪些模块包括了booster
'''
有4种方式,自动找到有@boost装饰器,注册booster

1. 用户亲自把要启动的消费函数所在模块或函数 手动 import 一下到此模块来
2. 用户在使用命令行时候 --import_modules_str 指定导入哪些模块路径,就能启动那些队列名来消费和发布了.
3. 用户使用BoosterDiscovery.auto_discovery_boosters  自动 import 指定文件夹下的 .py 文件来实现.
4  用户在使用命令行时候传参 project_root_path booster_dirs ,自动扫描模块,自动import
'''
env_dict['project_root_path'] = project_root_path

# booster_dirs 用户可以自己增加扫描的文件夹,这样可以命令行少传了 --booster_dirs_str
# BoosterDiscovery 可以多吃调用
BoosterDiscovery(project_root_path, booster_dirs=[], max_depth=1,py_file_re_str=None).auto_discovery()


if __name__ == '__main__':
    fire.Fire(BoosterFire, )

'''

python /codes/funboost/funboost_cli_user.py   --booster_dirs_str=test_frame/test_funboost_cli/test_find_boosters --max_depth=2  push test_find_queue1 --x=1 --y=2

python /codes/funboost/funboost_cli_user.py   --booster_dirs_str=test_frame/test_funboost_cli/test_find_boosters --max_depth=2  consume test_find_queue1 

'''
