# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/1/26
"""
WebSocket Broker - 基于 WebSocket 的消息队列

设计理念：
    - 使用 WebSocket 连接进行消息发布和消费
    - 支持实时双向通信
    - 适用于轻量级、实时性要求高的场景

使用方式：
    from websocket_broker import BROKER_KIND_WEBSOCKET
    
    @boost(BoosterParams(
        queue_name='ws_queue',
        broker_kind=BROKER_KIND_WEBSOCKET,
        broker_exclusive_config={
            'ws_url': 'ws://localhost:8765',
        }
    ))
    def process_message(x, y):
        return x + y
    
    if __name__ == '__main__':
        # 需要先启动 WebSocket 服务器
        process_message.consume()

依赖：
    pip install websocket-client
"""

import json
import threading
import time
import queue as queue_module
from typing import Optional
import logging
import re
import socket

try:
    import websocket
except ImportError:
    raise ImportError("请安装 websocket-client: pip install websocket-client")

from funboost import register_custom_broker, AbstractConsumer, AbstractPublisher
from funboost.core.broker_kind__exclusive_config_default_define import register_broker_exclusive_config_default
from funboost.core.loggers import get_funboost_file_logger

# ============================================================================
# Publisher 实现
# ============================================================================

class WebSocketPublisher(AbstractPublisher):
    """
    WebSocket 发布者
    
    通过 WebSocket 连接向服务器发送消息
    """
    
    def custom_init(self):
        config = self.publisher_params.broker_exclusive_config
        self._ws_url = config['ws_url']
        self._reconnect_interval = config['reconnect_interval']
        self._ws = None
        self._lock = threading.Lock()
        self._connect()
        self.logger.info(f"WebSocket Publisher 初始化完成，连接: {self._ws_url}")
    
    def _connect(self):
        """建立 WebSocket 连接"""
        try:
            self._ws = websocket.create_connection(
                self._ws_url,
                timeout=10,
            )
            self.logger.debug(f"WebSocket 连接成功: {self._ws_url}")
        except Exception as e:
            self.logger.warning(f"WebSocket 连接失败: {e}")
            self._ws = None
    
    def _ensure_connection(self):
        """确保连接有效"""
        with self._lock:
            if self._ws is None or not self._ws.connected:
                self._connect()
    
    def _publish_impl(self, msg: str):
        """
        发布消息：通过 WebSocket 发送
        """
        self._ensure_connection()
        if self._ws is None:
            raise ConnectionError("WebSocket 连接不可用")
        
        # 封装消息，添加队列名称
        envelope = {
            'command': 'publish',
            'queue': self._queue_name,
            'body': msg,
        }
        self._ws.send(json.dumps(envelope))
    
    def clear(self):
        """清空队列（WebSocket 不支持，发送清空命令给服务器）"""
        self._ensure_connection()
        if self._ws:
            cmd = {'command': 'clear', 'queue': self._queue_name}
            self._ws.send(json.dumps(cmd))
    
    def get_message_count(self) -> int:
        """获取队列消息数量（需要服务器支持）"""
        # WebSocket 本身不支持获取消息数量，返回 -1 表示未知
        return -1
    
    def close(self):
        """关闭连接"""
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None


# ============================================================================
# Consumer 实现
# ============================================================================

class WebSocketConsumer(AbstractConsumer):
    """
    WebSocket 消费者
    
    通过 WebSocket 连接接收消息并消费
    """
    
    BROKER_KIND = None  # 会被框架自动设置
    _server_started = False  # 类变量，标记服务器是否已启动
    _server_lock = threading.Lock()
    
    def _before_start_consuming_message_hook(self):
        config = self.consumer_params.broker_exclusive_config
        self._ws_url = config['ws_url']
        self._reconnect_interval = config['reconnect_interval']
        self._ws = None
        self._running = False
        self._message_queue = queue_module.Queue()
        
        # 自动启动 WebSocket 服务器（如果尚未启动）
        self._ensure_server_started()
        
        self.logger.info(f"WebSocket Consumer 初始化完成，连接: {self._ws_url}")
    
    def _ensure_server_started(self):
        """确保 WebSocket 服务器已启动"""
        with WebSocketConsumer._server_lock:
            if WebSocketConsumer._server_started:
                return
            
            # 解析 URL 获取 host 和 port
            
            match = re.match(r'ws://([^:]+):(\d+)', self._ws_url)
            if not match:
                self.logger.warning(f"无法解析 WebSocket URL: {self._ws_url}")
                return
            
            host = match.group(1)
            port = int(match.group(2))
            
            # 检查端口是否已被占用
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind((host, port))
                sock.close()
                # 端口可用，启动服务器
                self._start_server_in_background(host, port)
                WebSocketConsumer._server_started = True
            except OSError:
                # 端口已被占用，可能服务器已启动
                self.logger.info(f"WebSocket 服务器可能已在运行: {self._ws_url}")
                WebSocketConsumer._server_started = True
            finally:
                try:
                    sock.close()
                except Exception:
                    pass
    
    def _start_server_in_background(self, host, port):
        """在后台线程启动 WebSocket 服务器"""
        def _run():
            try:
                start_simple_ws_server(host=host, port=port)
            except Exception as e:
                self.logger.error(f"WebSocket 服务器异常: {e}")
        
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        time.sleep(0.5)  # 等待服务器启动
        self.logger.info(f"WebSocket 服务器已在后台启动: ws://{host}:{port}")
    
    def _connect(self):
        """建立 WebSocket 连接"""
        try:
            self._ws = websocket.create_connection(
                self._ws_url,
                timeout=30,
            )
            # 发送订阅命令
            subscribe_cmd = {
                'command': 'subscribe',
                'queue': self._queue_name,
            }
            self._ws.send(json.dumps(subscribe_cmd))
            self.logger.info(f"WebSocket 连接成功并订阅队列: {self._queue_name}")
            return True
        except Exception as e:
            self.logger.warning(f"WebSocket 连接失败: {e}")
            self._ws = None
            return False
    
    def _dispatch_task(self):
        """
        核心调度方法
        接收 WebSocket 消息并提交任务
        """
        self._running = True
        
        while self._running:
            # 确保连接
            if self._ws is None or not self._ws.connected:
                if not self._connect():
                    time.sleep(self._reconnect_interval)
                    continue
            
            try:
                # 接收消息（阻塞）
                raw_message = self._ws.recv()
                if not raw_message:
                    continue
                
                # 解析消息
                envelope = json.loads(raw_message)
                
                # 检查是否是目标队列的消息
                if envelope.get('queue') != self._queue_name:
                    continue
                
                body = envelope.get('body')
                if body is None:
                    continue
                
                # 如果 body 是字符串，解析为字典
                if isinstance(body, str):
                    body = json.loads(body)
                
                # 封装为 kw 并提交任务
                kw = {
                    'body': body,
                    'message_id': envelope.get('message_id'),
                }
                self._submit_task(kw)
                
            except websocket.WebSocketTimeoutException:
                # 超时是正常的，继续循环
                continue
            except websocket.WebSocketConnectionClosedException:
                self.logger.warning("WebSocket 连接已关闭，尝试重连...")
                self._ws = None
                time.sleep(self._reconnect_interval)
          
    
    def _confirm_consume(self, kw):
        """
        确认消费成功
        WebSocket 通常不需要 ACK，但可以发送确认命令给服务器
        """
        message_id = kw.get('message_id')
        if message_id and self._ws and self._ws.connected:
            try:
                ack_cmd = {
                    'command': 'ack',
                    'queue': self._queue_name,
                    'message_id': message_id,
                }
                self._ws.send(json.dumps(ack_cmd))
            except Exception as e:
                self.logger.debug(f"发送 ACK 失败: {e}")
    
    def _requeue(self, kw):
        """
        消息重入队
        发送重入队命令给服务器
        """
        message_id = kw.get('message_id')
        body = kw.get('body')
        if self._ws and self._ws.connected:
            try:
                requeue_cmd = {
                    'command': 'requeue',
                    'queue': self._queue_name,
                    'message_id': message_id,
                    'body': body,
                }
                self._ws.send(json.dumps(requeue_cmd))
            except Exception as e:
                self.logger.warning(f"重入队失败: {e}")


# ============================================================================
# 注册 Broker
# ============================================================================

BROKER_KIND_WEBSOCKET = 'WEBSOCKET'

register_broker_exclusive_config_default(
    BROKER_KIND_WEBSOCKET,
    {
        'ws_url': 'ws://localhost:8765',         # WebSocket 服务器地址
        'reconnect_interval': 5,                  # 重连间隔（秒）
    }
)

register_custom_broker(BROKER_KIND_WEBSOCKET, WebSocketPublisher, WebSocketConsumer)


# ============================================================================
# 简单的 WebSocket 服务器（用于测试）
# ============================================================================

logger_ws_server = get_funboost_file_logger('websocket_server',log_level_int=logging.INFO)

def start_simple_ws_server(host='localhost', port=8765):
    """
    启动一个简单的 WebSocket 服务器用于测试
    
    需要安装：pip install websockets
    """
    try:
        import asyncio
        import websockets
    except ImportError:
        raise ImportError("请安装 websockets: pip install websockets")
    
    # 存储订阅者（不缓存消息，WebSocket 是实时的）
    subscribers = {}  # {queue_name: [websocket]}
    
    async def handler(ws):
        logger_ws_server.info(f"新连接: {ws.remote_address}")
        subscribed_queue = None
        
        try:
            async for message in ws:
                data = json.loads(message)
                command = data.get('command')
                queue_name = data.get('queue')
                
                if command == 'subscribe':
                    # 订阅队列
                    subscribed_queue = queue_name
                    if queue_name not in subscribers:
                        subscribers[queue_name] = []
                    subscribers[queue_name].append(ws)
                    logger_ws_server.info(f"客户端订阅队列: {queue_name}")
                        
                elif command == 'clear':
                    # 清空（WebSocket 无缓存，无需处理）
                    pass
                    
                elif command == 'ack':
                    # ACK（WebSocket 模式不需要 ACK）
                    pass
                    
                elif command == 'requeue':
                    # 重入队：直接再次发送给订阅者
                    body = data.get('body')
                    if queue_name in subscribers:
                        requeue_msg = json.dumps({
                            'queue': queue_name,
                            'body': body,
                            'message_id': data.get('message_id'),
                        })
                        for subscriber in subscribers[queue_name]:
                            try:
                                await subscriber.send(requeue_msg)
                            except Exception as e:
                                logger_ws_server.error(f"重入队发送失败: {e}")
                    
                elif command == 'publish' or command is None:
                    # 发布消息：分发给订阅者，没有订阅者就丢弃
                    if queue_name in subscribers and subscribers[queue_name]:
                        for subscriber in subscribers[queue_name]:
                            try:
                                await subscriber.send(message)
                            except Exception as e:
                                print(f"发送失败（连接可能已关闭）: {e}")
                        logger_ws_server.debug(f"消息已分发: {queue_name}")
                    else:
                        logger_ws_server.warning(f"消息已丢弃（无订阅者）: {queue_name}")
                    
        except websockets.ConnectionClosed:
            logger_ws_server.info(f"连接正常关闭: {ws.remote_address}")
        finally:
            # 移除订阅者
            if subscribed_queue and subscribed_queue in subscribers:
                if ws in subscribers[subscribed_queue]:
                    subscribers[subscribed_queue].remove(ws)
    
    async def main():
        async with websockets.serve(handler, host, port):
            logger_ws_server.info(f"WebSocket 服务器启动: ws://{host}:{port}")
            await asyncio.Future()  # 永远运行
    
    asyncio.run(main())


if __name__ == '__main__':
    pass