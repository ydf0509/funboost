from nameko.standalone.rpc import ClusterRpcProxy

CONFIG = {'AMQP_URI': "amqp://admin:admin@192.168.64.151"}


def compute():
    with ClusterRpcProxy(CONFIG) as rpc:
        r = rpc.hello_service.hello(1,2)
        print(r)


if __name__ == '__main__':
    compute()
