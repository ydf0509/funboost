# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:32
import cgi
import io
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse

from funboost.consumers.base_consumer import AbstractConsumer


class HttpHandler(BaseHTTPRequestHandler):
    consumer = None  # type:AbstractConsumer

    def do_GET(self):
        parsed_path = parse.urlparse(self.path)
        message_parts = [
            'CLIENT VALUES:',
            'client_address={} ({})'.format(
                self.client_address,
                self.address_string()),
            'command={}'.format(self.command),
            'path={}'.format(self.path),
            'real path={}'.format(parsed_path.path),
            'query={}'.format(parsed_path.query),
            'request_version={}'.format(self.request_version),
            '',
            'SERVER VALUES:',
            'server_version={}'.format(self.server_version),
            'sys_version={}'.format(self.sys_version),
            'protocol_version={}'.format(self.protocol_version),
            '',
            'HEADERS RECEIVED:',
        ]
        for name, value in sorted(self.headers.items()):
            message_parts.append(
                '{}={}'.format(name, value.rstrip())
            )
        message_parts.append('')
        message = '\r\n'.join(message_parts)
        self.send_response(200)
        self.send_header('Content-Type',
                         'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))

    def do_POST(self):
        # 分析提交的表单数据
        # print(self.path)
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,  # noqa
            environ={
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': self.headers['Content-Type'],
            }
        )

        if self.path == '/queue':
            msg = form['msg'].value
            # print(msg)
            self.consumer._print_message_get_from_broker('http ', msg)
            kw = {'body': json.loads(msg)}
            self.consumer._submit_task(kw)

        # 开始回复
        self.send_response(200)
        self.send_header('Content-Type',
                         'text/plain; charset=utf-8')
        self.end_headers()

        out = io.TextIOWrapper(
            self.wfile,
            encoding='utf-8',
            line_buffering=False,
            write_through=True,
        )

        out.write('Client: {}\n'.format(self.client_address))
        out.write('User-agent: {}\n'.format(
            self.headers['user-agent']))
        out.write('Path: {}\n'.format(self.path))
        out.write('Form data:\n')
        # print(form.keys())
        # 表单信息内容回放
        for field in form.keys():
            field_item = form[field]
            if field_item.filename:
                # 字段中包含的是一个上传文件
                file_data = field_item.file.read()
                file_len = len(file_data)
                del file_data
                out.write(
                    '\tUploaded {} as {!r} ({} bytes)\n'.format(
                        field, field_item.filename, file_len)
                )
            else:
                # 通常形式的值
                out.write('\t{}={}\n'.format(
                    field, form[field].value))

        # 将编码 wrapper 到底层缓冲的连接断开，
        # 使得将 wrapper 删除时，
        # 并不关闭仍被服务器使用 socket 。
        out.detach()

class HTTPConsumer(AbstractConsumer, ):
    """
    http 实现消息队列，不支持持久化，但不需要安装软件。
    """
    BROKER_KIND = 23

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._ip, self._port = self.queue_name.split(':')
        self._port = int(self._port)

    # noinspection DuplicatedCode
    def _shedual_task(self):
        class CustomHandler(HttpHandler):
            consumer = self

        server = HTTPServer(('0.0.0.0', self._port), CustomHandler)
        print(f'Starting server, 0.0.0.0:{self._port}')
        server.serve_forever()

    def _confirm_consume(self, kw):
        pass  # 没有确认消费的功能。

    def _requeue(self, kw):
        pass
