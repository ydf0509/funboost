#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import grpc
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 导入生成的 protobuf 文件
import hello_pb2
import hello_pb2_grpc


def test_original():
    """
    原始版本 - 单线程同步调用
    """
    print("\n=== 测试1: 原始版本（单线程同步）===")
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = hello_pb2_grpc.HelloServiceStub(channel)
        
        time_start = time.time()
        for i in range(1000):  # 减少到1000次便于测试
            request = hello_pb2.HelloRequest(name=f"World_{i}")
            try:
                response = stub.SayHello(request)
                # 不打印，只接收
            except grpc.RpcError as e:
                print(f"gRPC 调用失败: {e}")
        time_end = time.time()
        total_time = time_end - time_start
        print(f"1000次调用耗时: {total_time:.3f} 秒")
        print(f"平均每次调用: {total_time/1000*1000:.3f} 毫秒")
        print(f"QPS: {1000/total_time:.0f}")


def test_channel_options():
    """
    优化版本1 - 使用连接池和优化的channel选项
    """
    print("\n=== 测试2: 优化Channel选项 ===")
    
    # 优化的channel选项
    options = [
        ('grpc.keepalive_time_ms', 10000),
        ('grpc.keepalive_timeout_ms', 5000),
        ('grpc.keepalive_permit_without_calls', True),
        ('grpc.http2.max_pings_without_data', 0),
        ('grpc.http2.min_time_between_pings_ms', 10000),
        ('grpc.http2.min_ping_interval_without_data_ms', 300000),
        ('grpc.max_connection_idle_ms', 30000),
    ]
    
    with grpc.insecure_channel('localhost:50051', options=options) as channel:
        stub = hello_pb2_grpc.HelloServiceStub(channel)
        
        time_start = time.time()
        for i in range(1000):
            request = hello_pb2.HelloRequest(name=f"World_{i}")
            try:
                response = stub.SayHello(request)
            except grpc.RpcError as e:
                print(f"gRPC 调用失败: {e}")
        time_end = time.time()
        total_time = time_end - time_start
        print(f"1000次调用耗时: {total_time:.3f} 秒")
        print(f"平均每次调用: {total_time/1000*1000:.3f} 毫秒")
        print(f"QPS: {1000/total_time:.0f}")


def test_thread_pool():
    """
    优化版本2 - 使用线程池并发调用
    """
    print("\n=== 测试3: 线程池并发调用 ===")
    
    def make_call(stub, i):
        request = hello_pb2.HelloRequest(name=f"World_{i}")
        try:
            response = stub.SayHello(request)
            return True
        except grpc.RpcError as e:
            print(f"gRPC 调用失败: {e}")
            return False
    
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = hello_pb2_grpc.HelloServiceStub(channel)
        
        time_start = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_call, stub, i) for i in range(1000)]
            
            success_count = 0
            for future in as_completed(futures):
                if future.result():
                    success_count += 1
                    
        time_end = time.time()
        total_time = time_end - time_start
        print(f"1000次调用耗时: {total_time:.3f} 秒")
        print(f"成功调用: {success_count}/1000")
        print(f"平均每次调用: {total_time/1000*1000:.3f} 毫秒")
        print(f"QPS: {1000/total_time:.0f}")


def test_multiple_connections():
    """
    优化版本3 - 使用多个连接
    """
    print("\n=== 测试4: 多连接并发 ===")
    
    def worker(worker_id, calls_per_worker):
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = hello_pb2_grpc.HelloServiceStub(channel)
            
            for i in range(calls_per_worker):
                request = hello_pb2.HelloRequest(name=f"Worker_{worker_id}_Call_{i}")
                try:
                    response = stub.SayHello(request)
                except grpc.RpcError as e:
                    print(f"Worker {worker_id} 调用失败: {e}")
    
    num_workers = 5
    calls_per_worker = 200  # 5*200 = 1000
    
    time_start = time.time()
    threads = []
    for worker_id in range(num_workers):
        thread = threading.Thread(target=worker, args=(worker_id, calls_per_worker))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
        
    time_end = time.time()
    total_time = time_end - time_start
    print(f"1000次调用耗时: {total_time:.3f} 秒")
    print(f"平均每次调用: {total_time/1000*1000:.3f} 毫秒")
    print(f"QPS: {1000/total_time:.0f}")


def test_batch_calls():
    """
    优化版本4 - 预创建请求对象，减少对象创建开销
    """
    print("\n=== 测试5: 预创建请求对象 ===")
    
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = hello_pb2_grpc.HelloServiceStub(channel)
        
        # 预创建所有请求对象
        requests = [hello_pb2.HelloRequest(name=f"World_{i}") for i in range(1000)]
        
        time_start = time.time()
        for request in requests:
            try:
                response = stub.SayHello(request)
            except grpc.RpcError as e:
                print(f"gRPC 调用失败: {e}")
        time_end = time.time()
        total_time = time_end - time_start
        print(f"1000次调用耗时: {total_time:.3f} 秒")
        print(f"平均每次调用: {total_time/1000*1000:.3f} 毫秒")
        print(f"QPS: {1000/total_time:.0f}")


if __name__ == '__main__':
    print("gRPC 性能测试对比")
    print("=" * 50)
    
    # 运行各种测试
    test_original()
    test_channel_options()
    test_batch_calls()
    test_thread_pool()
    test_multiple_connections()
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("\n分析:")
    print("1. 原始版本慢的原因:")
    print("   - 单线程同步调用，没有并发")
    print("   - 每次都创建新的请求对象")
    print("   - 没有优化gRPC连接参数")
    print("\n2. 优化建议:")
    print("   - 使用线程池或多连接实现并发")
    print("   - 预创建请求对象")
    print("   - 调整gRPC连接参数")
    print("   - 考虑使用异步gRPC (grpcio-async)")

