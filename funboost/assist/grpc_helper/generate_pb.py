#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
生成 protobuf 文件的脚本
运行此脚本来生成 funboost_grpc_pb2.py 和 funboost_grpc_pb2_grpc.py 文件
"""

import subprocess
import sys
import os


def generate_protobuf():
    """
    生成 protobuf 文件
    """
    try:
        # 执行 protoc 命令
        cmd = [
            sys.executable, '-m', 'grpc_tools.protoc',
            '--proto_path=.',
            '--python_out=.',
            '--grpc_python_out=.',
            'funboost_grpc.proto'
        ]
        
        print("正在生成 protobuf 文件...")
        print(f"执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ protobuf 文件生成成功！")
            print("生成的文件:")
            if os.path.exists('funboost_grpc_pb2.py'):
                print("  - funboost_grpc_pb2.py")
            if os.path.exists('funboost_grpc_pb2_grpc.py'):
                print("  - funboost_grpc_pb2_grpc.py")
        else:
            print("❌ protobuf 文件生成失败！")
            print(f"错误信息: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 生成过程中出现异常: {e}")


if __name__ == '__main__':
    generate_protobuf()
