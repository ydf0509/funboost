from funboost import boost, FunctionResultStatus,BoosterParams
import json

# from funboost.contrib.save_function_result_status.save_result_status_to_sqldb import save_result_status_to_sqlalchemy

"""
测试用户自定义记录函数消息处理的结果和状态到mysql

"""
from funboost.contrib.save_function_result_status.save_result_status_use_dataset import ResultStatusUseDatasetMixin

def my_save_process_info_fun(function_result_status: FunctionResultStatus):
    """ function_result_status变量上有各种丰富的信息 ,用户可以使用其中的信息
    用户自定义记录函数消费信息的钩子函数
    """
    print('function_result_status变量上有各种丰富的信息: ',
          function_result_status.task_id,
          function_result_status.publish_time, function_result_status.publish_time_format,
          function_result_status.params, function_result_status.msg_dict,
          function_result_status.time_cost, function_result_status.result,
          function_result_status.process_id, function_result_status.thread_id,
          function_result_status.host_process, )
    print('保存到数据库',json.dumps( function_result_status.get_status_dict()))

# user_custom_record_process_info_func=my_save_process_info_fun 设置记录函数消费状态的钩子
@boost(BoosterParams(queue_name='test_user_custom',
       # user_custom_record_process_info_func=save_result_status_to_sqlalchemy,
        consumer_override_cls=ResultStatusUseDatasetMixin,

       ))
def f(x):
    print(x * 10)
    return x*10


if __name__ == '__main__':
    for i in range(3):
        f.push(i)
    print(f.publisher.get_message_count())
    f.consume()
