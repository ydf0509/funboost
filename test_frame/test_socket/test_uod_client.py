import socket

BUFSIZE = 2
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
while True:
    msg = input(">> ").strip()
    ip_port = ('127.0.0.1', 9999)
    client.sendto(msg.encode('utf-8'), ip_port)

    data, server_addr = client.recvfrom(BUFSIZE)
    print('客户端recvfrom ', data, server_addr)

client.close()