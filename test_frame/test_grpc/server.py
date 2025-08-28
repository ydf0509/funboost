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
    HelloService 的实现类
    """
    
    def SayHello(self, request, context):
        """
        实现 SayHello 方法
        """
        message = f"Hello, {request.name}!"
        return hello_pb2.HelloResponse(message=message)


def serve():
    """
    启动 gRPC 服务器
    """
    # 创建服务器
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # 添加服务
    hello_pb2_grpc.add_HelloServiceServicer_to_server(HelloServicer(), server)
    
    # 绑定端口
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    
    # 启动服务器
    server.start()
    print(f"gRPC 服务器已启动，监听地址: {listen_addr}")
    
    try:
        while True:
            time.sleep(86400)  # 保持服务器运行
    except KeyboardInterrupt:
        print("正在关闭服务器...")
        server.stop(0)


if __name__ == '__main__':
    serve()
