import eventlet

eventlet.monkey_patch()
from nameko.containers import ServiceContainer
from nameko.rpc import rpc

class HelloService:
    name = "hello_service"

    @rpc
    def hello(self):
        print("hello world")


if __name__ == '__main__':
    '''
    nameko run nameko_server --broker amqp://admin:admin@192.168.64.151
    '''
    # from nameko.cli.run import run
    #
    # run([HelloService],  {'AMQP_URI': 'amqp://admin:admin@192.168.64.151'}, backdoor_port=None)



    container = ServiceContainer(HelloService, config={'AMQP_URI': 'amqp://admin:admin@192.168.64.151'})

    container.start()

    try:
        container.wait()
    except KeyboardInterrupt:
        container.kill()
    container.stop()