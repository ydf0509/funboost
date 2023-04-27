from nameko.standalone.rpc import ClusterRpcProxy

CONFIG = {'AMQP_URI': "amqp://admin:admin@192.168.64.151"}


def compute():
    with ClusterRpcProxy(CONFIG) as rpc:
        rpc.hello_service.hello()


if __name__ == '__main__':
    compute()
