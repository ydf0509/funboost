# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/8 0008 13:32

import abc
import threading
import grpc
import time

from funboost import FunctionResultStatus
from funboost.assist.grpc_helper import funboost_grpc_pb2_grpc, funboost_grpc_pb2
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.serialization import Serialization
from funboost.core.exceptions import FunboostWaitRpcResultTimeout
from funboost.concurrent_pool.flexible_thread_pool import FlexibleThreadPool


class FutureStatusResult:
    def __init__(self,call_type:str):
        self.execute_finish_event = threading.Event()
        self.staus_result_obj: FunctionResultStatus = None
        self.call_type  = call_type  # sync_call   or  publish

    def set_finish(self):
        self.execute_finish_event.set()

    def wait_finish(self,rpc_timeout):
        return self.execute_finish_event.wait(rpc_timeout)

    def set_staus_result_obj(self, staus_result_obj:FunctionResultStatus):
        self.staus_result_obj = staus_result_obj

    def get_staus_result_obj(self):
        return self.staus_result_obj




class GrpcConsumer(AbstractConsumer, ):
    """
     grpc as  broker
    """
    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'host': '127.0.0.1', 'port': None}

    def custom_init(self):
        class FunboostGrpcServicer(funboost_grpc_pb2_grpc.FunboostBrokerServiceServicer):
            """
            HelloService 的实现类
            """

            def Call(this, request, context):
                """
                实现 SayHello 方法
                """
                future_status_result = FutureStatusResult(call_type=request.call_type)
                kw = {'body': request.json_req, 'future_status_result': future_status_result,}
                self._submit_task(kw)
                if request.call_type =="sync_call":
                    if future_status_result.wait_finish(self.consumer_params.rpc_timeout):  # 等待并发出的消费结果
                        return funboost_grpc_pb2.FunboostGrpcResponse(json_resp=Serialization.to_json_str(
                            future_status_result.get_staus_result_obj().get_status_dict(without_datetime_obj=True)))
                    else:
                        self.logger.error(f'wait rpc data timeout')
                        context.set_code(grpc.StatusCode.DEADLINE_EXCEEDED)
                        context.set_details(f'wait rpc data timeout')
                        # raise FunboostWaitRpcResultTimeout(f'wait rpc data timeout')
                else:
                    return funboost_grpc_pb2.FunboostGrpcResponse(json_resp='{"publish_status":"ok"}')

        self.GRPC_SERVICER_CLS = FunboostGrpcServicer

    def _shedual_task(self):
        server = grpc.server(self.concurrent_pool)

        # 添加服务
        funboost_grpc_pb2_grpc.add_FunboostBrokerServiceServicer_to_server(self.GRPC_SERVICER_CLS(), server)

        # 绑定端口
        port = self.consumer_params.broker_exclusive_config['port']
        if port is None:
            raise ValueError('please specify port')
        listen_addr = f'[::]:{port}'
        server.add_insecure_port(listen_addr)

        # 启动服务器
        server.start()
        print(f"GRPC Has started. listening on: {listen_addr}")

        while True:
            time.sleep(100)  # 保持服务器运行

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        pass

    def _frame_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus, kw):
        future_status_result: FutureStatusResult = kw['future_status_result']
        if future_status_result.call_type == "sync_call":
            future_status_result.set_staus_result_obj(current_function_result_status)
            future_status_result.set_finish()  # 这是最重要最核心的, 并发池里面处理函数完成,马上告诉grpc服务端，已经处理完成.
