import re
import sys
import typing
from os import PathLike
from pathlib import Path
import importlib.util
# import nb_log
from funboost.core.loggers import FunboostFileLoggerMixin
from funboost.utils.decorators import flyweight
from funboost.core.lazy_impoter import lazy_impoter

@flyweight
class BoosterDiscovery(FunboostFileLoggerMixin):
    def __init__(self, project_root_path: typing.Union[PathLike, str],
                 booster_dirs: typing.List[typing.Union[PathLike, str]],
                 max_depth=1, py_file_re_str: str = None):
        """
        :param project_root_path 项目根目录
        :param booster_dirs: @boost装饰器函数所在的模块的文件夹,不用包含项目根目录长路径
        :param max_depth: 查找多少深层级子目录
        :param py_file_re_str: 文件名匹配过滤. 例如你所有的消费函数都在xxx_task.py yyy_task.py这样的,  你可以传参 task.py , 避免自动import了不需要导入的模块
        """

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
                spec = importlib.util.spec_from_file_location('module', file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
        lazy_impoter.BoostersManager.show_all_boosters()


if __name__ == '__main__':
    # 指定文件夹路径
    BoosterDiscovery(project_root_path='/codes/funboost',
                     booster_dirs=['test_frame/test_funboost_cli/test_find_boosters'],
                     max_depth=2, py_file_re_str='task').auto_discovery()
