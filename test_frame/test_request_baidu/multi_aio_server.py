import asyncio
import os
import socket
import time
from aiohttp import web


def mk_socket(host="127.0.0.1", port=8000, reuseport=False):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if reuseport:
        SO_REUSEPORT = 15
        sock.setsockopt(socket.SOL_SOCKET, SO_REUSEPORT, 1)
    sock.bind((host, port))
    return sock

async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    pid = os.getpid()
    text = "{:.2f}: Hello {}! Process {} is treating you\n".format(
        time.time(), name, pid)
    time.sleep(0.5)  # intentionally blocking sleep to simulate CPU load
    return web.Response(text=text)

if __name__ == '__main__':
    host = "127.0.0.1"
    port=8000
    reuseport = True
    app = web.Application()
    sock = mk_socket(host, port, reuseport=reuseport)
    app.add_routes([web.get('/', handle),
                    web.get('/{name}', handle)])
    loop = asyncio.get_event_loop()
    coro = loop.create_server(
        protocol_factory=app.make_handler(),
        sock=sock,
        )
    srv = loop.run_until_complete(coro)
    loop.run_forever()