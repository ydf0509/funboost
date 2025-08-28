#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import grpc

# 导入生成的 protobuf 文件
import hello_pb2
import hello_pb2_grpc
import time

def run_client():
    """
    运行 gRPC 客户端
    """
    # 连接到服务器
    with grpc.insecure_channel('localhost:50051') as channel:
        # 创建 stub
        stub = hello_pb2_grpc.HelloServiceStub(channel)
        time_start = time.time()
        for i in range(10000):
            # 创建请求
            request = hello_pb2.HelloRequest(name=f"World_{i}")
            
            try:
                # 调用远程方法
                response = stub.SayHello(request)
                # print(f"服务器响应: {response.message}")
            except grpc.RpcError as e:
                print(f"gRPC 调用失败: {e}")
        time_end = time.time()
        print(f"gRPC 调用时间: {time_end - time_start} 秒")


def interactive_client():
    """
    交互式客户端
    """
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = hello_pb2_grpc.HelloServiceStub(channel)
        
        while True:
            name = input("请输入您的名字 (输入 'quit' 退出): ")
            if name.lower() == 'quit':
                break
                
            request = hello_pb2.HelloRequest(name=name)
            
            try:
                response = stub.SayHello(request)
                print(f"服务器响应: {response.message}")
            except grpc.RpcError as e:
                print(f"gRPC 调用失败: {e}")
        



if __name__ == '__main__':
    print("=== gRPC 客户端测试 ===")
    print("1. 简单测试")
   
    run_client()
    
    # print("\n2. 交互式测试")
    # interactive_client()
