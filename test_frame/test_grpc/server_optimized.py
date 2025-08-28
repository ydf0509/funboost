#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import grpc
from concurrent import futures
import time

# 导入生成的 protobuf 文件
import hello_pb2
import hello_pb2_grpc


class HelloServicer(hello_pb2_grpc.HelloServiceServicer):
    """
    HelloService 的优化实现类
    """
    
    def SayHello(self, request, context):
        """
        实现 SayHello 方法 - 优化版本
        """
        # 直接返回，减少字符串拼接开销
        return hello_pb2.HelloResponse(message=f"Hello, {request.name}!")


def serve():
    """
    启动优化的 gRPC 服务器
    """
    # 优化的服务器选项
    options = [
        ('grpc.keepalive_time_ms', 10000),
        ('grpc.keepalive_timeout_ms', 5000),
        ('grpc.keepalive_permit_without_calls', True),
        ('grpc.http2.max_pings_without_data', 0),
        ('grpc.http2.min_time_between_pings_ms', 10000),
        ('grpc.http2.min_ping_interval_without_data_ms', 300000),
        ('grpc.max_connection_idle_ms', 30000),
        ('grpc.max_receive_message_length', 1024 * 1024 * 4),  # 4MB
        ('grpc.max_send_message_length', 1024 * 1024 * 4),     # 4MB
    ]
    
    # 增加线程池大小以处理更多并发请求
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=50),  # 增加到50个工作线程
        options=options
    )
    
    # 添加服务
    hello_pb2_grpc.add_HelloServiceServicer_to_server(HelloServicer(), server)
    
    # 绑定端口
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    
    # 启动服务器
    server.start()
    print(f"优化的 gRPC 服务器已启动，监听地址: {listen_addr}")
    print(f"工作线程数: 50")
    print("按 Ctrl+C 停止服务器")
    
    try:
        while True:
            time.sleep(86400)  # 保持服务器运行
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        server.stop(0)


if __name__ == '__main__':
    serve()

