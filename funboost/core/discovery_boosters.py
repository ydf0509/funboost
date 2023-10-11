import re
import sys
import typing
from os import PathLike
from pathlib import Path
import importlib.util
import nb_log
from funboost.core.global_boosters import show_all_boosters


class BoosterDiscovery(nb_log.LoggerMixin):
    def __init__(self, booster_dirs: typing.List[typing.Union[PathLike, str]], max_depth=1, py_file_re_str: str = None):
        """
        :param booster_dirs: @boost装饰器函数所在的模块的文件夹
        :param max_depth: 查找多少深层级子目录
        :param py_file_re_str: 文件名匹配过滤. 例如只import task_xx.py的,你可以传参 task , 避免自动import不需要导入的文件
        """

        self.booster_dirs = booster_dirs
        self.max_depth = max_depth
        self.py_file_re_str = py_file_re_str

        self.py_files = []

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
                        self.py_files.append(item)
                else:
                    self.py_files.append(item)
        for f in self.py_files:
            self.logger.debug(f)

    def auto_discovery(self, ):
        """把所有py文件自动执行import"""
        for dir in self.booster_dirs:
            if not Path(dir).exists():
                raise Exception(f'没有这个文件夹 ->  {dir}')

            self.get_py_files_recursively(Path(dir))
            for file_path in self.py_files:
                spec = importlib.util.spec_from_file_location('module', file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
        show_all_boosters()


if __name__ == '__main__':
    # 指定文件夹路径
    BoosterDiscovery([r'D:\codes\funboost\test_frame\test_funboost_cli\test_find_boosters'],
                     max_depth=2, py_file_re_str='task').auto_discovery()
