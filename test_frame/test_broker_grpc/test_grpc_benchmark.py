

from test_frame.test_broker_grpc.test_grpc_consumer import f,f2






if __name__ == '__main__':
    for i in range(100):
        f2.push(i,i*2)

