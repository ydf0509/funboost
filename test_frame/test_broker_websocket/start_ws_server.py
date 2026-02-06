# -*- coding: utf-8 -*-
"""
启动 WebSocket 测试服务器

直接运行此脚本即可启动服务器
"""

from websocket_broker import start_simple_ws_server

if __name__ == '__main__':
    print("=" * 50)
    print("WebSocket 测试服务器")
    print("=" * 50)
    print("监听地址: ws://localhost:8765")
    print("按 Ctrl+C 停止")
    print("=" * 50)
    
    start_simple_ws_server(host='localhost', port=8765)
