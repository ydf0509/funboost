import sys
from pathlib import Path

project_root_path = str(Path(__file__).absolute().parent.parent.parent)
print(f'project_root_path is : {project_root_path}')
sys.path.insert(1, project_root_path)  # 这个是为了方便命令行不用用户手动先 export PYTHONPATTH=项目根目录

##### $$$$$$$$$$$$
#  以上的代码要放在最上面,先设置好pythonpath再导入funboost相关的.
##### $$$$$$$$$$$$


from funboost.core.funboost_fire import funboost_fire
from funboost.utils.ctrl_c_end import ctrl_c_recv
# 需要启动的函数,那么该模块或函数建议一定要被import到这来. 否则需要要在 --import_modules_str 中指定
# noinspection PyUnresolvedReferences
import def_tasks  # 这是为了导入被boost装饰的函数,这个重要,不然不知道队列对应的函数在哪里

# def_tasks3.py 文件由于没有导入,如果想操作def_tasks3的队列,那么需要  --import_modules_str

if __name__ == '__main__':
    funboost_fire()
    # ctrl_c_recv()

    '''
    
    如果没写sys.path.insert(1,项目根目录),那么需要先set PYTHONPATH=项目根目录
    set PYTHONPATH=/codes/funboost/ 
    
    
    python test_cli.py clear test_cli1_queue   # 清空消息队列
    
    python test_cli.py push test_cli1_queue 1 2  # 发布消息
    python test_cli.py push test_cli1_queue 1 --y=2 # 发布消息,也可以明显点传入参名字
    python test_cli.py publish test_cli1_queue "{'x':3,'y':4}"  # 发布消息传递一个字典
    python test_cli.py publish test_cli1_queue '{"x":3,"y":4}' # 错误方式
    
    
    python test_cli.py consume test_cli1_queue test_cli2_queue  # 启动两个队列的函数消费
    python test_cli.py m_consume --test_cli1_queue=2 --test_cli2_queue=3 # 叠加多进程启动消费
    
    # 发布消息,由于当前代码没有import def_tasks3模块,所以需要传递入参 import_modules_str,然后再发布
    # 如果需要导入多个模块,import_modules_str的值使用逗号隔开
    python test_cli.py --import_modules_str "test_frame.test_funboost_cli.def_tasks3"  publish test_cli3_queue "{'x':3,'y':4}"
    
    # 如果没有亲自import boost函数所在模块,则可以自动扫描文件夹下的py文件,自动import
    python test_cli.py --boost_dirs_str './test_find_boosters,./test_find_boosters/d2'  push test_find_queue1 --x=1 --y=2
    
    '''

    '''
    cd D:\codes\funboost\test_frame\test_funboost_cli && python test_cli.py consume test_cli1_queue test_cli2_queue
    '''
