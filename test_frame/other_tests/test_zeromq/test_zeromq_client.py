import zmq,time

#  Prepare our context and sockets
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5559")

#  Do 10 requests, waiting each time for a response
for request in range(1,11):
    time.sleep(2)
    socket.send(f"Hello {request}".encode())
    message = socket.recv()
    print("Received reply %s [%s]" % (request, message))
