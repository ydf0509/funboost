# typing.TYPE_CHECKING 详解

## 什么是 TYPE_CHECKING？

`typing.TYPE_CHECKING` 是一个在**运行时为 False**，但在**类型检查时为 True** 的特殊常量。

```python
import typing
print(typing.TYPE_CHECKING)  # 输出: False
```

## 主要作用

### 1. 避免循环导入 (Circular Imports)

**问题场景：**
```python
# teacher.py
from student import Student  # 导入Student

class Teacher:
    def __init__(self):
        self.students: List[Student] = []

# student.py  
from teacher import Teacher  # 导入Teacher - 循环导入！

class Student:
    def __init__(self):
        self.teacher: Teacher = None
```

**解决方案：**
```python
# teacher.py
import typing
if typing.TYPE_CHECKING:
    from student import Student  # 只在类型检查时导入

class Teacher:
    def __init__(self):
        self.students: typing.List['Student'] = []  # 使用字符串注解
```

### 2. 性能优化 - 避免导入昂贵模块

**问题场景：**
```python
import pandas as pd  # 很重的库，导入慢
import numpy as np   # 很重的库，导入慢

def simple_function(data: pd.DataFrame) -> np.ndarray:
    # 这个函数可能很简单，不需要真正使用pandas
    return data
```

**解决方案：**
```python
import typing
if typing.TYPE_CHECKING:
    import pandas as pd  # 只在类型检查时导入
    import numpy as np

def simple_function(data: 'pd.DataFrame') -> 'np.ndarray':
    # 运行时不会导入pandas，提高启动速度
    return data
```

### 3. 前向引用 (Forward References)

**问题场景：**
```python
class Node:
    def add_child(self, child: Node) -> None:  # 错误！Node还没定义完
        pass
```

**解决方案：**
```python
class Node:
    def add_child(self, child: 'Node') -> None:  # 使用字符串
        pass
    
    # 或者使用TYPE_CHECKING
    if typing.TYPE_CHECKING:
        def method(self, other: Node) -> None:  # 可以直接使用
            pass
```

### 4. 条件类型定义

```python
if typing.TYPE_CHECKING:
    # 复杂的类型定义，只在类型检查时需要
    ComplexType = typing.Union[str, int, typing.Dict[str, typing.Any]]
else:
    # 运行时使用简单类型
    ComplexType = object
```

## 为什么原来的代码会报错？

在原来的 `broker_kind__exclusive_config_default_define.py` 中：

```python
import typing
if typing.TYPE_CHECKING:
    import logging  # 只在类型检查时导入

def generate_broker_exclusive_config(
    broker_kind: str, 
    user_broker_exclusive_config: dict, 
    logger: logging.Logger  # 运行时访问logging，但logging没有导入！
):
    pass
```

**问题：**
1. `logging` 只在 `TYPE_CHECKING=True` 时导入
2. 但运行时 `TYPE_CHECKING=False`，所以 `logging` 没有导入
3. 函数签名 `logger: logging.Logger` 在运行时需要访问 `logging`
4. 结果：`NameError: name 'logging' is not defined`

**正确的做法：**

**方案1：** 移出TYPE_CHECKING（我们采用的）
```python
import logging  # 运行时也导入
```

**方案2：** 使用字符串注解
```python
if typing.TYPE_CHECKING:
    import logging

def generate_broker_exclusive_config(
    broker_kind: str, 
    user_broker_exclusive_config: dict, 
    logger: 'logging.Logger'  # 使用字符串
):
    pass
```

## 总结

`TYPE_CHECKING` 的核心思想是：
- **类型检查时**：提供完整的类型信息
- **运行时**：避免不必要的导入和性能开销

使用场景：
1. 解决循环导入
2. 避免导入重型库
3. 处理前向引用
4. 条件类型定义

**关键原则：** 如果类型注解在运行时会被访问（如函数签名），要么真正导入模块，要么使用字符串形式的类型注解。
