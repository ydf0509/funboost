import typing
import inspect
import copy
from funboost.core.func_params_model import BoosterParams,PublisherParams
from funboost.core.loggers import FunboostFileLoggerMixin
from funboost.constant import ConsumingFuncInputParamsCheckerField
from funboost.core.exceptions import FuncParamsError


class ConsumingFuncInputParamsChecker(FunboostFileLoggerMixin):
    """
    发布的任务的函数参数检查，使发布的任务在消费时候不会出现低级错误。
    """

    def __init__(self, final_func_input_params_list_info: typing.Dict):
        self.update_check_params(final_func_input_params_list_info)

    def update_check_params(self,final_func_input_params_list_info): 
        """这个是供动态热更新校验参数，funboost.faas 不重启就能动态变更函数修改后的校验规则
        因为 funboost.faas 完全不需要依赖真正的消费函数对象，
        是把保存到redis元数据的booster_params的 auto_generate_info.final_func_input_params_info 更新到ConsumingFuncInputParamsChecker实例中
        
        redis中的 auto_generate_info 例子如下
        "auto_generate_info": {
    "where_to_instantiate": "D:\\codes\\funboost\\examples\\example_faas\\task_funs_dir\\sub.py:5",
    "final_func_input_params_info": {
      "func_name": "sub",
      "func_position": "<function sub at 0x00000272649BBA60>",
      "is_manual_func_input_params": false,
      "all_arg_name_list": [
        "a",
        "b"
      ],
      "must_arg_name_list": [
        "a",
        "b"
      ],
      "optional_arg_name_list": []
    }
  }
        """
        self.consuming_func_input_params_list_info = final_func_input_params_list_info
        self.all_arg_name_list = final_func_input_params_list_info[ConsumingFuncInputParamsCheckerField.all_arg_name_list]
        self.all_arg_name_set = set(self.all_arg_name_list)
        self.position_arg_name_set = set(final_func_input_params_list_info[ConsumingFuncInputParamsCheckerField.must_arg_name_list])
        self.optional_arg_name_set = set(final_func_input_params_list_info[ConsumingFuncInputParamsCheckerField.optional_arg_name_list])


    @staticmethod
    def gen_func_params_info_by_func(func: typing.Callable):
        spec = inspect.getfullargspec(func)
        all_arg_name_list = list(spec.args)
        all_arg_name_set = set(spec.args)
        # print(spec.args)
        if spec.defaults:
            len_deafult_args = len(spec.defaults)
            position_arg_name_list = spec.args[0: -len_deafult_args]
            position_arg_name_set = set(position_arg_name_list)
            keyword_arg_name_list = spec.args[-len_deafult_args:]
            keyword_arg_name_set = set(keyword_arg_name_list)
        else:
            position_arg_name_list = spec.args
            position_arg_name_set = set(position_arg_name_list)
            keyword_arg_name_list = []
            keyword_arg_name_set = set()
        # print(func.__name__,str(func),func)
        consuming_func_input_params_list_info = {
            ConsumingFuncInputParamsCheckerField.func_name: func.__name__,
            ConsumingFuncInputParamsCheckerField.func_position: str(func),
            ConsumingFuncInputParamsCheckerField.is_manual_func_input_params: False,
            ConsumingFuncInputParamsCheckerField.all_arg_name_list: all_arg_name_list,
            ConsumingFuncInputParamsCheckerField.must_arg_name_list: position_arg_name_list,
            ConsumingFuncInputParamsCheckerField.optional_arg_name_list: keyword_arg_name_list,
        }
        return consuming_func_input_params_list_info

    def check_func_msg_dict(self, publish_params: dict):
        publish_params_keys_set = set(publish_params.keys())
        if publish_params_keys_set.issubset(self.all_arg_name_set) and publish_params_keys_set.issuperset(self.position_arg_name_set):
            return True
        else:
            error_data = {
            'your_now_publish_params_keys_list':list(publish_params_keys_set),
            'right_func_input_params_list_info':self.consuming_func_input_params_list_info,
            }
            raise FuncParamsError('Invalid parameters for consuming function',error_data=error_data)


    @classmethod
    def gen_final_func_input_params_info(cls,consumer_or_publisher_params:typing.Union[BoosterParams,PublisherParams]):
        """
        生成最终的函数参数信息，包括手动输入的参数和默认参数。
        """
        auto_generate_info = consumer_or_publisher_params.auto_generate_info
        if 'final_func_input_params_info' in auto_generate_info:
            return
        else:
            auto_generate_info['final_func_input_params_info'] = {}
        if consumer_or_publisher_params.manual_func_input_params['is_manual_func_input_params'] is False :
            consuming_func_input_params_list_info =  cls.gen_func_params_info_by_func(consumer_or_publisher_params.consuming_function)
            auto_generate_info['final_func_input_params_info'].update(consuming_func_input_params_list_info)
        if  consumer_or_publisher_params.manual_func_input_params['is_manual_func_input_params'] is True:
            manual_func_input_params_new = copy.deepcopy(consumer_or_publisher_params.manual_func_input_params)
            manual_func_input_params_new[ConsumingFuncInputParamsCheckerField.is_manual_func_input_params] = True
            manual_func_input_params_new[ConsumingFuncInputParamsCheckerField.all_arg_name_list] = manual_func_input_params_new[ConsumingFuncInputParamsCheckerField.must_arg_name_list] + manual_func_input_params_new[ConsumingFuncInputParamsCheckerField.optional_arg_name_list]
            manual_func_input_params_new['func_name'] = getattr(consumer_or_publisher_params.consuming_function,'__name__',None)
            # print(consumer_or_publisher_params.consuming_function,str(consumer_or_publisher_params.consuming_function))
            manual_func_input_params_new['func_position'] = str(consumer_or_publisher_params.consuming_function)
            auto_generate_info['final_func_input_params_info'].update(manual_func_input_params_new)





class FakeFunGenerator:
    """
    动态函数生成器：根据参数元数据生成具有正确签名的伪函数
    用途：funboost.faas 可以从 redis 元数据动态生成函数对象，无需真正的函数定义
    """
    
    @staticmethod
    def gen_fake_fun_by_params(final_func_input_params_info:dict):
        """
        根据必需参数和可选参数列表动态生成函数
        你可以理解是为了欺骗 inspect 模块，让 inspect 模块返回的函数参数信息和实际的函数参数信息一致。
        函数名、参数列表、默认值和原函数一模一样
        """

        must_arg_name_list = final_func_input_params_info[ConsumingFuncInputParamsCheckerField.must_arg_name_list]
        optional_arg_name_list = final_func_input_params_info[ConsumingFuncInputParamsCheckerField.optional_arg_name_list]
        func_name = final_func_input_params_info[ConsumingFuncInputParamsCheckerField.func_name]
        
        
        # 构建参数字符串
        must_params = ', '.join(must_arg_name_list)
        optional_params = ', '.join([f'{arg}=None' for arg in optional_arg_name_list])
        
        # 组合所有参数
        if must_params and optional_params:
            all_params = f'{must_params}, {optional_params}'
        elif must_params:
            all_params = must_params
        elif optional_params:
            all_params = optional_params
        else:
            all_params = ''
        
        # 动态生成函数代码
        func_code = f'''
def {func_name}({all_params}):
    """
    Dynamically generated function with signature:
    - Required params: {must_arg_name_list}
    - Optional params: {optional_arg_name_list}
    """
    return locals()
'''
        
        # 执行代码生成函数
        local_namespace = {}
        exec(func_code, {}, local_namespace)
        fake_fun = local_namespace[func_name]
        setattr(fake_fun,'is_fake_fun',True)
        return fake_fun
    
    @staticmethod
    def gen_fake_fun():
        """随便生成的假的函数，这种需要 update_check_params去更新"""
        def fake_fun():
            pass
        setattr(fake_fun,'is_fake_fun',True)
        return fake_fun
    

    @staticmethod
    def is_fake_fun(func):
        return getattr(func,'is_fake_fun',False)