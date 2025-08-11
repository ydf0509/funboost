import os
import warnings
from celery import Celery


def make_celery() -> Celery:
    """创建 Celery 应用（支持无 Broker 回退到 eager 同进程执行）。

    环境变量：
    - CELERY_BROKER_URL: 如 `redis://127.0.0.1:6379/0` 或 `pyamqp://guest@localhost//`
    - CELERY_RESULT_BACKEND: 如 `redis://127.0.0.1:6379/0` 或 `rpc://`
    """

    broker_url = os.getenv("CELERY_BROKER_URL", "").strip()
    result_backend = os.getenv("CELERY_RESULT_BACKEND", "").strip()

    app = Celery("test_celery_canvas")

    if not broker_url:
        # 无外部 Broker 场景：退回到单进程 eager 模式，便于快速体验
        warnings.warn(
            "未检测到 CELERY_BROKER_URL，已启用 task_always_eager 模式（单进程本地执行）。\n"
            "如需真正的分布式并发与监控，请设置 Redis/RabbitMQ 等 Broker 并启动 worker。",
            RuntimeWarning,
        )
        app.conf.update(
            broker_url="memory://",
            result_backend="cache+memory://",
            task_always_eager=True,
            task_eager_propagates=True,
            task_ignore_result=False,
        )
    else:
        if not result_backend:
            if broker_url.startswith("redis://"):
                result_backend = broker_url
            else:
                # 默认使用 RPC 结果后端（需 AMQP）
                result_backend = "rpc://"
        app.conf.update(
            broker_url=broker_url,
            result_backend=result_backend,
            task_always_eager=False,
        )

    app.conf.update(
        timezone="Asia/Shanghai",
        enable_utc=False,
        task_acks_late=True,
        worker_hijack_root_logger=False,
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        result_expires=3600,
        task_default_queue="canvas_default",
        task_routes={
            "test_frame.test_celery_canvas.tasks.fetch_url": {"queue": "io"},
            "test_frame.test_celery_canvas.tasks.sleep_task": {"queue": "io"},
            "test_frame.test_celery_canvas.tasks.retryable_task": {"queue": "cpu"},
        },
        task_annotations={
            "test_frame.test_celery_canvas.tasks.rate_limited_task": {"rate_limit": "10/m"}
        },
    )

    # 自动发现任务
    app.autodiscover_tasks(["test_frame.test_celery_canvas"])
    return app


app = make_celery()


