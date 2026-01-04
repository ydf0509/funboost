这个问题是因为代码中使用了 `@flyweight` 装饰器，而传递给被装饰函数的参数中包含了不可哈希（unhashable）的类型（例如 `list` 列表）。

**详细原因：**

1.  **报错位置**：你的 traceback 指向 `funboost/utils/decorators.py` 的 `_make_key` 函数中 `return (args, frozenset(kwds.items()))` 这一行。
2.  **原理**：`@flyweight` 是一个享元模式（或单例模式变种）的装饰器，它会缓存类的实例。为了区分不同的实例，它需要根据传入的参数（`args` 和 `kwargs`）生成一个唯一的 **Cache Key**。
3.  **冲突点**：生成 Key 时使用了 `frozenset` 和 `tuple`，这些结构要求其包含的元素必须是 **可哈希的 (hashable)**。
    *   在你的场景中，`BoosterDiscovery` 类的 `__init__` 方法接收了一个参数 `booster_dirs`，它是一个列表 (`list`)，例如 `['your_booster_dir']`。
    *   **Python 中的 `list` 是不可哈希的**（因为它是可变的），所以当 `_make_key` 尝试将其放入 `frozenset` 时，就报了 `TypeError: unhashable type: 'list'`。

**解决方案：**

我已经修改了 `funboost/utils/decorators.py` 文件，增强了 `_make_key` 函数。现在它会自动检测参数类型，如果发现是 `list`、`dict` 或 `set`，会自动将它们转换为可哈希的 `tuple` 或 `frozenset`。这意味着你不需要修改任何业务代码，原来的调用方式现在可以正常工作了。

**修改后的核心代码逻辑：**

```python
    def _make_hashable(value):
        if isinstance(value, dict):
            return tuple(sorted((k, _make_hashable(v)) for k, v in value.items()))
        elif isinstance(value, (list, tuple)):
            return tuple(_make_hashable(v) for v in value)
        elif isinstance(value, set):
            return frozenset(_make_hashable(v) for v in value)
        return value

    def _make_key(args, kwds):
        # ...
        key_args = _make_hashable(args)
        key_kwargs = frozenset((k, _make_hashable(v)) for k, v in kwds.items())
        # ...
```

现在你可以重试运行你的代码，应该不会再报这个错了。
