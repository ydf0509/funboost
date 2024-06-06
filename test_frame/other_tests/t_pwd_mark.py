from typing import Protocol, runtime_checkable


# 假设我们有一个StringProtocol，但在这里我们不会列出str的所有方法
@runtime_checkable
class StringProtocol(Protocol):
    # 示例方法，实际StringProtocol会包含str的所有方法
    def __str__(self) -> str:
        ...

    def upper(self) -> str:
        ...
        # ... 其他str方法 ...


# MyString类，它封装了一个str对象，并提供了一些额外的功能或属性
class MyString:
    def __init__(self, value: str):
        self._value = value

    def __str__(self) -> str:
        return self._value

    def __getattr__(self, name: str) -> any:
        # 如果MyString没有该属性或方法，则尝试从_value（一个str对象）中获取
        return getattr(self._value, name)

        # 添加其他自定义方法...


# 示例使用
my_string = MyString("hello")
print(my_string.upper())  # 输出: HELLO

import queue


# 注意：尽管MyString没有直接继承StringProtocol，但它通过__getattr__实现了类似的行为
# 在静态类型检查器中（如mypy），如果使用了StringProtocol，MyString可能不会被识别为完全符合该协议
# 除非使用了额外的类型注解或检查器配置来识别这种动态代理模式