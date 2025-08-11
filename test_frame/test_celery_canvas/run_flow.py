import argparse
import json
import os
from typing import List

from . import run_flow_by_name


def parse_args():
    p = argparse.ArgumentParser(description="Run Celery canvas demo flows")
    p.add_argument("flow", help="flow name, e.g. chain_basics")
    p.add_argument("--urls", nargs="*", default=[
        "https://httpbin.org/get",
        "https://www.example.com",
    ], help="urls for http fetch flow")
    p.add_argument("--numbers", nargs="*", type=int, default=[1, 2, 3, 4, 5], help="numbers list")
    p.add_argument("--video-url", default="https://example.com/video.mp4", help="video url for video pipeline demo")
    return p.parse_args()


def main():
    args = parse_args()
    flow = args.flow
    urls: List[str] = list(args.urls)
    numbers: List[int] = list(args.numbers)

    result = None

    if flow == "chain_basics":
        result = run_flow_by_name(flow, 3, 5)
    elif flow == "group_chord":
        result = run_flow_by_name(flow, urls)
    elif flow == "chord_with_error_callback":
        result = run_flow_by_name(flow, numbers)
    elif flow == "nested_chain_group":
        result = run_flow_by_name(flow, numbers)
    elif flow == "map_and_starmap":
        result = run_flow_by_name(flow, numbers)
    elif flow == "chain_link_error_ignored":
        result = run_flow_by_name(flow)
    elif flow == "complex_mix":
        result = run_flow_by_name(flow, urls, numbers)
    elif flow == "video_pipeline":
        result = run_flow_by_name(flow, args.video_url)
    else:
        raise SystemExit(f"Unknown flow: {flow}")

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


