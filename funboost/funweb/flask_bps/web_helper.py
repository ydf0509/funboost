
# -*- coding: utf-8 -*-
"""SSE 日志实时推送最长持续时间（秒）。

部署详情、日志查看器的前端脚本中 LOG_STREAM_MAX_MS 须与此值一致（×1000 为毫秒）。
"""
import socket
import os

LOG_STREAM_MAX_SECONDS = 300


def _get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = socket.gethostbyname(socket.gethostname())
    return ip

def _get_local_hostname():
    return socket.gethostname()

# LOCAL_IP = _get_local_ip()  # win 不同网络，ip容易变化

LOCAL_IP = _get_local_hostname()

if os.getenv('FUNWEB_LOCAL_IP'): # 如果环境变量 FUNWEB_LOCAL_IP 存在，则使用环境变量 FUNWEB_LOCAL_IP 的值
    LOCAL_IP = os.getenv('FUNWEB_LOCAL_IP')