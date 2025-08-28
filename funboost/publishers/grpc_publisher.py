import abc
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.assist.grpc_helper import funboost_grpc_pb2_grpc, funboost_grpc_pb2
from funboost.core.serialization import Serialization
from funboost.core.function_result_status_saver import FunctionResultStatus
import grpc


class GrpcPublisher(AbstractPublisher, ):
    """grpc 作为broker"""

    def custom_init(self):
        host = self.publisher_params.broker_exclusive_config['host']
        port = self.publisher_params.broker_exclusive_config['port']
        channel = grpc.insecure_channel(f'{host}:{port}')
        stub = funboost_grpc_pb2_grpc.FunboostBrokerServiceStub(channel)
        self._stub = stub
        self._channel = channel

    def concrete_realization_of_publish(self, msg: str):
        request = funboost_grpc_pb2.FunboostGrpcRequest(json_req=msg,call_type="publish")
        response = self._stub.Call(request)
        return response.json_resp

    def sync_call(self, msg_dict: dict, is_return_rpc_data_obj=True):
        """
        同步请求,并阻塞等待结果返回.
        不像push那样依赖AsyncResult + redis 实现的rpc
        :param msg_dict:
        :return:
        """

        """
        用法例子
        $booster.publisher.grpc_call({'x':i,'y':i*2}) 
        """
        request = funboost_grpc_pb2.FunboostGrpcRequest(json_req=Serialization.to_json_str(msg_dict),
                                                        call_type="sync_call")
        response = self._stub.Call(request)
        json_resp =  response.json_resp
        if is_return_rpc_data_obj:
            return FunctionResultStatus.parse_status_and_result_to_obj(Serialization.to_dict(json_resp))
        else:
            return Serialization.to_dict(json_resp)

    def clear(self):
        pass

    def get_message_count(self):
        return -1

    def close(self):
        self._channel.close()
