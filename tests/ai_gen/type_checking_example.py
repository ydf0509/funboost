"""
演示 typing.TYPE_CHECKING 的作用和用法
"""
import typing

# 案例1: 避免循环导入
if typing.TYPE_CHECKING:
    # 这些导入只在类型检查时执行，运行时不执行
    from some_heavy_module import HeavyClass
    from collections.abc import Callable
    import logging

# 案例2: 前向引用问题
class Node:
    def __init__(self, value: int, parent: typing.Optional['Node'] = None):
        self.value = value
        self.parent = parent
        self.children: typing.List['Node'] = []
    
    # 在 TYPE_CHECKING 中可以直接使用类型
    if typing.TYPE_CHECKING:
        def add_child(self, child: Node) -> None:  # 可以直接用 Node
            pass
    else:
        def add_child(self, child: 'Node') -> None:  # 运行时需要字符串
            self.children.append(child)

# 案例3: 避免导入昂贵的模块
def process_data(data: typing.Any) -> typing.Any:
    """
    如果我们只是为了类型注解需要导入一个很大的模块，
    可以把导入放在 TYPE_CHECKING 中
    """
    # 实际处理逻辑
    return data

# 如果直接导入会影响性能
if typing.TYPE_CHECKING:
    import pandas as pd
    import numpy as np

def analyze_dataframe(df: 'pd.DataFrame') -> 'np.ndarray':
    """
    使用字符串形式的类型注解，避免运行时导入pandas和numpy
    """
    # 实际函数可能不需要这些库，只是为了类型提示
    return df.values

# 案例4: 解决循环导入
# 假设有两个模块互相引用的情况
class Teacher:
    def __init__(self, name: str):
        self.name = name
        if typing.TYPE_CHECKING:
            # 只在类型检查时导入，避免循环导入
            from student_module import Student
        self.students: typing.List['Student'] = []

# 案例5: 运行时和类型检查时的不同行为
if typing.TYPE_CHECKING:
    # 类型检查时使用精确的类型
    LoggerType = logging.Logger
else:
    # 运行时使用简单的类型或Any
    LoggerType = typing.Any

def setup_logging(logger: LoggerType) -> None:
    """
    这样可以避免运行时导入logging模块（如果不需要的话）
    """
    pass

# 案例6: 条件类型定义
if typing.TYPE_CHECKING:
    # 只在类型检查时定义这些复杂类型
    JsonDict = typing.Dict[str, typing.Any]
    CallbackFunc = typing.Callable[[str], None]
else:
    # 运行时使用简单定义
    JsonDict = dict
    CallbackFunc = object

def process_json(data: JsonDict, callback: CallbackFunc) -> None:
    """使用条件定义的类型"""
    pass

print("TYPE_CHECKING 在运行时的值:", typing.TYPE_CHECKING)
print("这个文件可以正常运行，不会导入TYPE_CHECKING块中的模块")
