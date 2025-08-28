# gRPC Demo

这是一个最简单的 gRPC 示例，演示了如何创建 gRPC 服务器和客户端。

## 文件说明

- `hello.proto` - protobuf 定义文件，定义了服务接口和消息格式
- `server.py` - gRPC 服务器实现
- `client.py` - gRPC 客户端实现
- `generate_pb.py` - 生成 protobuf 文件的脚本
- `requirements.txt` - Python 依赖包

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 生成 protobuf 文件

```bash
python generate_pb.py
```

这会生成 `hello_pb2.py` 和 `hello_pb2_grpc.py` 文件。

### 3. 启动服务器

```bash
python server.py
```

服务器将在 `localhost:50051` 上启动。

### 4. 运行客户端

在另一个终端中运行：

```bash
python client.py
```

## 示例输出

**服务器端：**
```
gRPC 服务器已启动，监听地址: [::]:50051
```

**客户端：**
```
=== gRPC 客户端测试 ===
1. 简单测试
服务器响应: Hello, World!

2. 交互式测试
请输入您的名字 (输入 'quit' 退出): Alice
服务器响应: Hello, Alice!
请输入您的名字 (输入 'quit' 退出): quit
```

## 工作原理

1. **proto 文件定义**：定义了 `HelloService` 服务，包含 `SayHello` 方法
2. **服务器**：实现 `HelloService`，接收客户端请求并返回问候消息
3. **客户端**：连接到服务器，发送请求并接收响应

这是一个最基础的 gRPC 示例，展示了 gRPC 的基本工作流程。
