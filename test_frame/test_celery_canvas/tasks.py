import os
import random
import time
from typing import Any, Dict, Iterable, List, Tuple

import requests
from celery import shared_task, states
from celery.exceptions import Ignore, Retry
import uuid


@shared_task(bind=True, name="test_frame.test_celery_canvas.tasks.add")
def add(self, x: int, y: int) -> int:
    return x + y


@shared_task(bind=True, name="test_frame.test_celery_canvas.tasks.mul")
def mul(self, x: int, y: int) -> int:
    return x * y


@shared_task(bind=True, name="test_frame.test_celery_canvas.tasks.sleep_task")
def sleep_task(self, seconds: float) -> float:
    time.sleep(seconds)
    return seconds


@shared_task(bind=True, name="test_frame.test_celery_canvas.tasks.fetch_url")
def fetch_url(self, url: str, timeout: int = 5) -> Dict[str, Any]:
    try:
        start = time.time()
        r = requests.get(url, timeout=timeout)
        elapsed = time.time() - start
        return {
            "url": url,
            "status": r.status_code,
            "elapsed_s": round(elapsed, 3),
            "length": len(r.content),
        }
    except requests.RequestException as exc:
        raise self.retry(exc=exc, countdown=2, max_retries=2)


@shared_task(bind=True, name="test_frame.test_celery_canvas.tasks.retryable_task", autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=10, retry_jitter=True, max_retries=3)
def retryable_task(self, value: int) -> int:
    if random.random() < 0.5:
        raise ValueError(f"transient error for {value}")
    return value * 10


@shared_task(bind=True, name="test_frame.test_celery_canvas.tasks.error_prone")
def error_prone(self, x: int) -> int:
    if x % 2 == 0:
        raise RuntimeError("Even number not allowed")
    return x


@shared_task(bind=True, name="test_frame.test_celery_canvas.tasks.on_error_collect")
def on_error_collect(self, request: Dict[str, Any], exc: str, traceback_str: str) -> Dict[str, Any]:
    # 作为 chord error callback 使用
    return {"task_id": request.get("id"), "exc": str(exc), "traceback": traceback_str[:400]}


@shared_task(bind=True, name="test_frame.test_celery_canvas.tasks.aggregate_dicts")
def aggregate_dicts(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = sum(item.get("length", 0) for item in results)
    status_2xx = sum(1 for item in results if 200 <= item.get("status", 0) < 300)
    return {"total_length": total, "ok": status_2xx, "count": len(results)}


@shared_task(bind=True, name="test_frame.test_celery_canvas.tasks.concat_strings")
def concat_strings(self, items: Iterable[str]) -> str:
    return ",".join(items)


@shared_task(bind=True, name="test_frame.test_celery_canvas.tasks.raise_ignore")
def raise_ignore(self, reason: str) -> None:
    self.update_state(state=states.IGNORED, meta={"reason": reason})
    raise Ignore()


@shared_task(bind=True, name="test_frame.test_celery_canvas.tasks.sum_list")
def sum_list(self, numbers: List[int]) -> int:
    return sum(numbers)


@shared_task(bind=True, name="test_frame.test_celery_canvas.tasks.to_pair")
def to_pair(self, x: int) -> Tuple[int, int]:
    return (x, x + 1)


# ---------------- Video pipeline demo tasks ----------------

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


@shared_task(bind=True, name="test_frame.test_celery_canvas.tasks.download_video")
def download_video(self, url: str) -> str:
    """模拟下载视频，生成到 tests/ai_gen/videos 下并返回文件路径。"""
    base_dir = os.path.join("tests", "ai_gen", "videos")
    _ensure_dir(base_dir)
    file_name = f"video_{uuid.uuid4().hex}.mp4"
    file_path = os.path.join(base_dir, file_name)

    # 模拟下载耗时
    time.sleep(0.2)
    with open(file_path, "wb") as f:
        content = f"dummy video from {url}".encode("utf-8")
        f.write(content)
    return file_path


@shared_task(bind=True, name="test_frame.test_celery_canvas.tasks.transform_video")
def transform_video(self, file_path: str, resolution: str = "720p") -> str:
    """模拟转码，读取输入文件并写入一个标记分辨率的新文件，返回新文件路径。"""
    out_dir = os.path.join("tests", "ai_gen", "videos", "transformed")
    _ensure_dir(out_dir)
    base = os.path.splitext(os.path.basename(file_path))[0]
    out_path = os.path.join(out_dir, f"{base}_{resolution}.mp4")

    # 模拟转码耗时
    time.sleep(0.1)
    with open(out_path, "wb") as f:
        f.write(f"transformed {resolution} from {file_path}".encode("utf-8"))
    return out_path


@shared_task(bind=True, name="test_frame.test_celery_canvas.tasks.send_finish_msg")
def send_finish_msg(self, transformed_files: List[str], url: str) -> Dict[str, Any]:
    """模拟发送完成消息，返回结果概要。"""
    return {"url": url, "files": transformed_files, "count": len(transformed_files)}


