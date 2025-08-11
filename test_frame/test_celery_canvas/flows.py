from __future__ import annotations

import traceback
from typing import Any, Dict, List, Tuple

from celery import chain, chord, group, signature

from .celery_app import app
from .tasks import (
    add,
    aggregate_dicts,
    concat_strings,
    download_video,
    error_prone,
    fetch_url,
    mul,
    on_error_collect,
    raise_ignore,
    send_finish_msg,
    retryable_task,
    sleep_task,
    sum_list,
    to_pair,
)


def flow_chain_basics(x: int = 3, y: int = 5) -> Any:
    # 链式： (x + y) * 8
    c = chain(add.s(x, y), mul.s(8))
    return c.apply_async().get()


def flow_group_and_chord(urls: List[str]) -> Dict[str, Any]:
    # group 并行抓取 -> chord 汇总
    g = group(fetch_url.s(url) for url in urls)
    result = chord(g)(aggregate_dicts.s()).get()
    return result


def flow_chord_with_error_callback(values: List[int]) -> Dict[str, Any]:
    # 有失败时触发自定义 error 回调
    g = group(error_prone.s(v) for v in values)
    try:
        res = chord(g)(sum_list.s()).get()
        return {"ok": True, "sum": res}
    except Exception as exc:  # 捕获 chord 异常，触发自定义收集
        tb = traceback.format_exc()
        collected = on_error_collect.apply_async(kwargs={"request": {}, "exc": str(exc), "traceback_str": tb}).get()
        return {"ok": False, "error": collected}


def flow_nested_chain_group(values: List[int]) -> List[Any]:
    # 嵌套：chain 中包含 group，再接后续任务
    g = group(retryable_task.s(v) for v in values)
    c = chain(g, sum_list.s())
    return c.apply_async().get()


def flow_map_and_starmap(numbers: List[int]) -> Tuple[List[int], List[int]]:
    # map: 将列表作为单参数映射
    mapped = group(add.s(n, 1) for n in numbers).apply_async().get()
    # starmap: 将多个参数展开
    pairs = group(to_pair.s(n) for n in numbers).apply_async().get()
    starmapped = group(mul.s(a, b) for a, b in pairs).apply_async().get()
    return mapped, starmapped


def flow_chain_link_error_ignored() -> Dict[str, Any]:
    # 某步返回 Ignore，不影响后续（链会被中断，需用 link_error 或 try/except 兜底）
    try:
        c = chain(raise_ignore.s("skip"), add.s(1))
        res = c.apply_async().get()
        return {"reached": True, "res": res}
    except Exception as exc:
        return {"reached": False, "exc": str(exc)}


def flow_complex_mix(urls: List[str], numbers: List[int]) -> Dict[str, Any]:
    # 复杂组合：
    # - chord(fetch_url) -> aggregate
    # - chain(sum_list(numbers), mul(2))
    # - group(retryable_task(numbers))
    # 最后汇总 concat_strings
    chord_part = chord(group(fetch_url.s(u) for u in urls))(aggregate_dicts.s())
    chain_part = chain(group(add.s(n, 0) for n in numbers), sum_list.s(), mul.s(2))
    retry_part = group(retryable_task.s(v) for v in numbers)

    g = group(
        signature("celery.accumulate").s([1, 2, 3]),  # Celery 内置示例（若不可用忽略结果）
        chord_part,
        chain_part,
        retry_part,
        sleep_task.s(0.2),
    )
    results = g.apply_async().get(propagate=False)

    # 处理内置任务不存在或失败的情况
    pretty = []
    for item in results:
        try:
            if isinstance(item, Exception):
                pretty.append(f"EXC:{item}")
            else:
                pretty.append(str(item))
        except Exception as exc:
            pretty.append(f"EXC:{exc}")

    summary = concat_strings.apply_async(args=[pretty]).get()
    return {"items": pretty, "summary": summary}


def flow_video_pipeline(url: str) -> Dict[str, Any]:
    """将 funboost 示例转换为 Celery canvas：

    等价流程：
    chain(download_video(url), chord(group(transform_video(file, r) for r in [360p,720p,1080p]), send_finish_msg(files, url)))
    
    表达为：先下载得到 file -> header(group) 生成多个分辨率 -> body 收敛并发送完成消息。
    """
    # 1) 先下载视频
    # 2) header: 对下载结果文件并行转码
    header = group(
        download_video.s(url) | signature("test_frame.test_celery_canvas.tasks.transform_video").s(res)
        for res in ["360p", "720p", "1080p"]
    )
    # 3) body: 汇总并发送完成消息（body 的参数接收 header 的列表结果）
    body = send_finish_msg.s(url=url)
    ch = chord(header, body)
    return ch.apply_async().get()


FLOWS = {
    "chain_basics": flow_chain_basics,
    "group_chord": flow_group_and_chord,
    "chord_with_error_callback": flow_chord_with_error_callback,
    "nested_chain_group": flow_nested_chain_group,
    "map_and_starmap": flow_map_and_starmap,
    "chain_link_error_ignored": flow_chain_link_error_ignored,
    "complex_mix": flow_complex_mix,
    "video_pipeline": flow_video_pipeline,
}


def run_flow_by_name(name: str, *args, **kwargs):
    fn = FLOWS.get(name)
    if not fn:
        raise KeyError(f"unknown flow: {name}")
    return fn(*args, **kwargs)


