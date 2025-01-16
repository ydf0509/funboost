


from dubbo import DubboServer
class HelloService:
    def hello(self, name):
        return f"Hello, {name}"
server = DubboServer(port=20880)
server.add_service("com.example.HelloService", HelloService())
server.start()
