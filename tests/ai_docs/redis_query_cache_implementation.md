# Redis查询缓存功能实现说明

## 概述

为 `RedisReportInfoGetterMixin` 类添加了30秒缓存机制，用于缓存Redis查询结果，减少频繁的Redis查询，提升性能。

## 实现方式

### 类属性缓存（所有实例共享）

使用**类属性**而不是实例属性，原因是：
- `RedisReportInfoGetterMixin` 允许多次实例化
- 使用类属性可以让所有实例共享同一个缓存
- 避免每个实例都重复查询Redis

### 缓存的类属性

```python
class RedisReportInfoGetterMixin:
    # 类属性：所有实例共享的缓存
    _cache_all_queue_names = None              # 缓存所有队列名称
    _cache_all_queue_names_ts = 0              # 缓存时间戳
    _cache_queue_names_by_project = {}         # 按项目名称缓存 {project_name: {'data': [...], 'ts': timestamp}}
    _cache_ttl = 30                            # 缓存有效期30秒
    _cache_lock = threading.Lock()             # 线程锁保证线程安全
```

## 缓存的方法

### 1. `get_all_queue_names()`

获取所有队列名称，带30秒缓存。

**工作流程：**
1. 检查缓存是否存在且未过期（30秒内）
2. 如果缓存有效，直接返回缓存结果
3. 如果缓存失效，从Redis查询
4. 更新缓存和时间戳

**示例：**
```python
# 创建实例1
getter1 = ActiveCousumerProcessInfoGetter()
result1 = getter1.get_all_queue_names()  # 从Redis查询

# 创建实例2
getter2 = ActiveCousumerProcessInfoGetter()
result2 = getter2.get_all_queue_names()  # 使用实例1的缓存，不查询Redis
```

### 2. `get_queue_names_by_project_name(project_name)`

根据项目名称获取队列名称，带30秒缓存。

**工作流程：**
1. 检查该项目的缓存是否存在且未过期
2. 如果缓存有效，直接返回缓存结果
3. 如果缓存失效，从Redis查询
4. 更新该项目的缓存

**示例：**
```python
getter = QueuesConusmerParamsGetter()
result1 = getter.get_queue_names_by_project_name('project1')  # 从Redis查询
result2 = getter.get_queue_names_by_project_name('project1')  # 使用缓存
result3 = getter.get_queue_names_by_project_name('project2')  # 不同项目，从Redis查询
```

## 线程安全

使用 `threading.Lock()` 保证线程安全：
- 读取缓存前加锁
- 更新缓存时加锁
- 避免多线程同时访问时出现竞态条件

```python
with self._cache_lock:
    if self._cache_all_queue_names is not None and (current_time - self._cache_all_queue_names_ts) < self._cache_ttl:
        return self._cache_all_queue_names
```

## 性能提升

### 缓存命中时的性能提升

- **首次查询：** 需要访问Redis，耗时约 0.001-0.01 秒
- **缓存命中：** 直接返回内存数据，耗时约 0.000001-0.00001 秒
- **速度提升：** 约 100-1000 倍

### 适用场景

特别适合以下场景：
1. Web管理后台频繁刷新队列列表
2. 监控面板定时轮询队列状态
3. 多个消费者实例同时查询队列信息
4. 高并发场景下的队列信息查询

## 缓存过期机制

- **缓存时间：** 30秒
- **过期后：** 自动从Redis重新查询
- **无需手动清理：** 缓存会自动过期更新

## 影响的类

由于使用了Mixin模式，以下类都继承了缓存功能：

1. **ActiveCousumerProcessInfoGetter** - 获取活跃消费进程信息
2. **QueuesConusmerParamsGetter** - 获取所有队列配置参数和运行信息  
3. **SingleQueueConusmerParamsGetter** - 获取单个队列配置参数和运行信息

所有这些类的实例都会共享同一个缓存。

## 测试

运行测试文件验证功能：

```bash
python tests/ai_codes/test_class_level_cache.py
```

测试内容包括：
- ✓ 多个实例共享类级别缓存
- ✓ 缓存过期机制
- ✓ 按项目名称查询的缓存
- ✓ 线程安全性

## 注意事项

1. **缓存有效期：** 默认30秒，可以修改 `_cache_ttl` 类属性
2. **实时性要求：** 如果需要实时数据，等待缓存过期或重启应用
3. **内存占用：** 缓存数据量较小，对内存影响可忽略
4. **线程安全：** 已使用线程锁保证，可以在多线程环境使用

## 配置调整

如需调整缓存时间，可以修改类属性：

```python
# 修改缓存时间为60秒
RedisReportInfoGetterMixin._cache_ttl = 60

# 或者在子类中重写
class MyGetter(ActiveCousumerProcessInfoGetter):
    _cache_ttl = 60  # 60秒缓存
```

## 总结

这个缓存机制通过以下方式提升性能：
1. ✓ 使用类属性让所有实例共享缓存
2. ✓ 30秒缓存时间平衡实时性和性能
3. ✓ 线程锁保证多线程安全
4. ✓ 自动过期机制无需手动管理
5. ✓ 极大减少Redis查询次数

