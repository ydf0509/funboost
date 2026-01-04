"""
【⚠️ 安全警示 & 最佳实践】

1. 关于 BoosterDiscovery 自动扫描的风险提示
-------------------------------------------------------
BoosterDiscovery(....).auto_discovery() 请务必谨慎使用，强烈建议实例化时传入精确的过滤参数。

原因：
    部分开发者的编程习惯可能不严谨，对于包含执行动作的脚本，未添加 `if __name__ == '__main__':` 保护，
    或者不理解 `__main__` 的作用。Python 的 import 机制意味着“导入即执行模块顶层代码”。

危险场景假设：
    假设项目中存在一个临时的脏数据清理脚本 `my_temp_dangerous_delete_mysql_script.py`：

    ```python
    # ❌ 危险写法：写在模块顶层，不在函数内，也无 main 保护
    import db_client
    db_client.execute("DROP TABLE users") 
    ```

后果：
    如果你使用了无限制的 `auto_discovery()`，即使项目上线2年后，一旦扫描并 import 到这个脚本，
    数据库表会在瞬间被删除。这绝对是生产事故级别的灾难。

✅ 正确用法（精确传参）：
    BoosterDiscovery(
        project_root_path='/path/to/your_project', 
        booster_dirs=['your_booster_dir'],
        max_depth=1,
        py_file_re_str='tasks'  # 强烈建议：只扫描包含 'tasks' 的文件，避开临时脚本
    ).auto_discovery()


2. 为什么推荐“显式 Import”而非“自动扫描”？BoosterDiscovery不是funboost的必需品！
-------------------------------------------------------
其实不建议过度依赖 `auto_discovery()`，更推荐的最佳实践是：
👉 手动明确 import 包含 @boost 的模块。需要用到哪些消费函数，就导入哪些模块。

Funboost vs Celery 的架构差异：
    * Funboost：
      没有中央 `app` 实例，不需要像 Celery 那样有一个单独的 `celery_app.py` 模块。
      架构上天然不存在“互相依赖导入”的死结。因此，要用什么消费函数，直接导入即可，简单直观。

    * Celery：
      必须手写 `includes` 配置或调用 `autodiscover_tasks()`。
      根本原因是：Celery 的 `xx_tasks.py` 需要导入 `celery_app.py` 中的 `app` 对象；
      而 `celery worker` 启动 `app` 时又需要导入 `xx_tasks.py` 来注册任务。
      这种设计导致双方陷入“循环导入”的死结，迫使 Celery 发明了一套复杂的导入机制，
      也让新手在规划目录结构时小心翼翼、非常纠结。
""" 

import re
import sys
import typing
from os import PathLike
from pathlib import Path
import importlib.util
# import nb_log
from funboost.core.loggers import FunboostFileLoggerMixin
from funboost.utils.decorators import flyweight
from funboost.core.lazy_impoter import funboost_lazy_impoter

# @flyweight
class BoosterDiscovery(FunboostFileLoggerMixin):
    def __init__(self, project_root_path: typing.Union[PathLike, str],
                 booster_dirs: typing.List[typing.Union[PathLike, str]],
                 max_depth=1, py_file_re_str: str = None):
        """
        :param project_root_path 项目根目录
        :param booster_dirs: @boost装饰器函数所在的模块的文件夹,不用包含项目根目录长路径
        :param max_depth: 查找多少深层级子目录
        :param py_file_re_str: 文件名匹配过滤. 例如你所有的消费函数都在xxx_task.py yyy_task.py这样的,  你可以传参 task.py , 避免自动import了不需要导入的模块
        
        BoosterDiscovery(....).auto_discovery() 需要谨慎使用，谨慎传参，原因见上面模块注释。
        
        """
        self.project_root_path = project_root_path
        self.booster__full_path_dirs = [Path(project_root_path) / Path(boost_dir) for boost_dir in booster_dirs]
        self.max_depth = max_depth
        self.py_file_re_str = py_file_re_str

        self.py_files = []
        self._has_discovery_import = False

    def get_py_files_recursively(self, current_folder_path: Path, current_depth=0, ):
        """先找到所有py文件"""
        if current_depth > self.max_depth:
            return
        for item in current_folder_path.iterdir():
            if item.is_dir():
                self.get_py_files_recursively(item, current_depth + 1)
            elif item.suffix == '.py':
                if self.py_file_re_str:
                    if re.search(self.py_file_re_str, str(item), ):
                        self.py_files.append(str(item))
                else:
                    self.py_files.append(str(item))
        self.py_files = list(set(self.py_files))

    def auto_discovery(self, ):
        """把所有py文件自动执行import,主要是把 所有的@boost函数装饰器注册到 pid_queue_name__booster_map 中
        这个auto_discovery方法最好放到main里面,如果要扫描自身文件夹,没写正则排除文件本身,会无限懵逼死循环导入,无无限懵逼死循环导入
        """
        if self._has_discovery_import is False:
            self._has_discovery_import = True
        else:
            pass
            return  # 这一个判断是避免用户执行BoosterDiscovery.auto_discovery没有放到 if __name__ == '__main__'中,导致无限懵逼死循环.
        self.logger.info(self.booster__full_path_dirs)
        for dir in self.booster__full_path_dirs:
            if not Path(dir).exists():
                raise Exception(f'没有这个文件夹 ->  {dir}')

            self.get_py_files_recursively(Path(dir))
            for file_path in self.py_files:
                self.logger.debug(f'导入模块 {file_path}')
                if Path(file_path) == Path(sys._getframe(1).f_code.co_filename):
                    self.logger.warning(f'排除导入调用auto_discovery的模块自身 {file_path}')  # 否则下面的import这个文件,会造成无限懵逼死循环
                    continue

                # module_name = Path(file_path).as_posix().replace('/', '.') + '.' + Path(file_path).stem
                module_name = Path(file_path).relative_to(Path(self.project_root_path)).with_suffix('').as_posix().replace('/', '.').replace('\\', '.')
                # print(module_name, file_path)
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
        funboost_lazy_impoter.BoostersManager.show_all_boosters()


if __name__ == '__main__':
    # 指定文件夹路径
    BoosterDiscovery(project_root_path='/codes/funboost',
                     booster_dirs=['test_frame/test_funboost_cli/test_find_boosters'],
                     max_depth=2, py_file_re_str='task').auto_discovery()
