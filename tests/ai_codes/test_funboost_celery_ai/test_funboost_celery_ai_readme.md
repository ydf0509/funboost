---
noteId: "99ba0e4021e911f18bc955817d43f5bc"
tags: []

---

示了如何使用 Funboost 框架配合 Celery 作为消息队列 broker。

## 依赖项

在运行本示例之前，需要安装以下依赖：

```bash
# 安装 Funboost
pip install funboost

# 安装 Celery 及其依赖
pip install celery

# 安装 Flower（用于监控 Celery，可选）
pip install flower

# 安装 Redis（作为 Celery 的消息存储，默认配置）
pip install redis
```

## 运行步骤

1. **启动 Redis 服务**
   - Celery 默认使用 Redis 作为消息存储，所以需要先启动 Redis 服务
   - 如果你没有 Redis，可以修改 Celery 配置使用其他 broker

2. **运行示例**
   - 执行 `test_funboost_celery_ai.py` 文件：
   ```bash
   python test_funboost_celery_ai.py
   ```

3. **查看任务执行情况**
   - 脚本会启动 Celery Worker 和 Flower 监控
   - 可以通过浏览器访问 `http://localhost:5555` 查看 Flower 监控界面

## 代码说明

1. **任务定义**
   - 使用 `@boost` 装饰器定义任务函数
   - 指定 `broker_kind=BrokerEnum.CELERY` 来使用 Celery 作为 broker
   - 可以通过 `broker_exclusive_config` 传递 Celery 特定的配置

2. **任务发布**
   - 使用 `push` 方法发布任务
   - 发布的任务会被 Celery 处理

3. **消费者启动**
   - 使用 `consume()` 方法启动消费者
   - 内部会自动配置 Celery 并启动 Worker

4. **监控**
   - 使用 `CeleryHelper.start_flower()` 启动 Flower 监控
   - 使用 `CeleryHelper.realy_start_celery_worker()` 启动 Celery Worker

## 注意事项

- 本示例使用默认的 Redis 配置，如果你需要使用其他 broker，请修改 Celery 配置
- 在生产环境中，建议在单独的进程中启动 Celery Worker
- 如果遇到依赖问题，可以参考 `test_funboost_celery_broker.py` 文件中的依赖版本建议

## 常见问题

### Linux 系统上 Celery 报错 "EntryPoints' object has no attribute 'get'"？

这是由于依赖版本不兼容导致的，可以尝试安装特定版本的依赖：

```bash
pip install frozenlist==1.3.1 geopy==2.2.0 humanize==4.3.0 idna==3.3 importlib-metadata==4.12.0 jsonschema==4.9.0 korean_lunar_calendar==0.2.1 marshmallow==3.17.0 pyOpenSSL==22.0.0 pyrsistent==0.18.1 python-dotenv==0.20.0 pytz==2022.2.1 selenium==4.4.0 simplejson==3.17.6 sniffio==1.2.0 trio==0.21.0 urllib3==1.26.11 wsproto==1.1.0 zipp==3.8.1
```

如果上述安装仍未解决，则执行以下安装：

```bash
pip install backoff==2.1.2 colorama==0.4.5 croniter==1.3.5 cryptography==37.0.4 email-validator==1.2.1 flask-compress==1.12 flask-migrate==3.1.0 aiohttp==3.8.1 aiosignal==1.2.0 Mako==1.2.1 Babel==2.10.3
```
