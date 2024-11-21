from dubbo.client import DubboClient
client = DubboClient("127.0.0.1:20880")
result = client.invoke("com.example.HelloService.hello", "World")
print(result)  # 输出: Hello, World