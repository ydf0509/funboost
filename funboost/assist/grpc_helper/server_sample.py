#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading

import grpc
from concurrent import futures
import time

# 导入生成的 protobuf 文件
import funboost_grpc_pb2
import funboost_grpc_pb2_grpc


class FunboostGrpcServicer(funboost_grpc_pb2_grpc.FunboostBrokerServiceServicer):
    """
    HelloService 的实现类
    """
    
    def Call(self, request, context):
        """
        实现 SayHello 方法
        """
        event = threading.Event()
        res = process_msg(request.json_req,event)
        event.wait(600)

        return funboost_grpc_pb2.FunboostGrpcResponse(json_resp=res)


def process_msg(x,event:threading.Event):
    time.sleep(3)
    event.set()
    return f'{{"respx":{x}}}'


def serve():
    """
    启动 gRPC 服务器
    """
    # 创建服务器
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # 添加服务
    funboost_grpc_pb2_grpc.add_FunboostBrokerServiceServicer_to_server(FunboostGrpcServicer(), server)
    
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
