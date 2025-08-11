### Celery Canvas 复杂编排示例

本示例演示 Celery 的 chain/group/chord、嵌套、map/starmap、错误回调、重试与忽略等用法。支持两种模式：

- 单机无 Broker（默认）：本地 eager 同进程执行，方便快速体验
- 分布式（推荐）：配置 Redis/RabbitMQ，启动 worker 并观察真正的并行与容错

#### 1) 安装依赖

```bash
pip install celery[redis]==5.3.6 requests
```

#### 2) 运行方式 A：本地 eager 模式（不需要 broker）

直接运行某个 Flow：

```bash
python -m test_frame.test_celery_canvas.run_flow chain_basics
python -m test_frame.test_celery_canvas.run_flow group_chord --urls https://httpbin.org/get https://www.example.com
python -m test_frame.test_celery_canvas.run_flow chord_with_error_callback --numbers 1 2 3 4 5
python -m test_frame.test_celery_canvas.run_flow nested_chain_group --numbers 1 2 3 4 5
python -m test_frame.test_celery_canvas.run_flow map_and_starmap --numbers 1 2 3 4 5
python -m test_frame.test_celery_canvas.run_flow chain_link_error_ignored
python -m test_frame.test_celery_canvas.run_flow complex_mix --urls https://httpbin.org/get https://www.example.com --numbers 1 2 3 4 5
python -m test_frame.test_celery_canvas.run_flow video_pipeline --video-url https://example.com/video.mp4
```

#### 3) 运行方式 B：分布式 Worker 模式（需要 broker）

设置环境变量：

```bash
set CELERY_BROKER_URL=redis://127.0.0.1:6379/0
set CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
```

启动 worker（Windows 建议使用 eventlet/gevent 或在 WSL/Linux/Mac 上运行）：

```bash
celery -A test_frame.test_celery_canvas.celery_app:app worker -l info -Q canvas_default,io,cpu
```

另一个终端运行 Flow，同上步骤 2 的命令。

#### 4) 目录结构

- `celery_app.py`: 应用初始化，支持 eager 回退
- `tasks.py`: 示例任务集合（加法、乘法、HTTP 请求、重试、错误、Ignore、聚合等）
- `flows.py`: 多种编排示例，含 chain/group/chord 嵌套
- `run_flow.py`: 命令行入口


