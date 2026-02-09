# -*- coding: utf-8 -*-
"""
启动 WebSocket 消费者

Consumer 会自动启动 WebSocket 服务器，无需手动启动
"""

import time
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent))

from funboost import BrokerEnum
from funboost import boost, BoosterParams


@boost(BoosterParams(
    queue_name='test_websocket_queue',
    broker_kind=BrokerEnum.WEBSOCKET,
    # qps=10,
    concurrent_num=3,
    log_level=logging.INFO,
    broker_exclusive_config={
        'ws_url': 'ws://localhost:8765',
        'reconnect_interval': 3,
    }
))
def process_message(x, y):
    """处理 WebSocket 消息"""
    result = x + y
    if x % 1000 == 0:
        print(f"处理消息: {x} + {y} = {result}")
    return result


if __name__ == '__main__':
    print("=" * 50)
    print("WebSocket 消费者")
    print("=" * 50)
    print("服务器将自动启动，按 Ctrl+C 停止")
    print("=" * 50)
    
    process_message.consume()
