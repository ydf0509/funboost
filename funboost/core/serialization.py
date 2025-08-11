import typing
import json
import orjson
import pickle
import ast

class Serialization:
    @staticmethod
    def to_json_str(dic:typing.Union[dict,str]):
        if isinstance(dic,str):
            return dic
        str1 =orjson.dumps(dic)
        return str1.decode('utf8')

    @staticmethod
    def to_dict(strx:typing.Union[str,dict]):
        if isinstance(strx,dict):
            return strx
        return orjson.loads(strx)
    
    @staticmethod
    def find_can_not_json_serializable_keys(dic:dict)->list[str]:
        can_not_json_serializable_keys = []
        dic = Serialization.to_dict(dic)
        for k,v in dic.items():
            if not isinstance(v,str):
                try:
                    json.dumps(v)
                except:
                    can_not_json_serializable_keys.append(k)
        return can_not_json_serializable_keys
    

class PickleHelper:
    @staticmethod
    def to_str(obj_x:typing.Any):
        return str(pickle.dumps(obj_x)) # 对象pickle,转成字符串
    
    @staticmethod
    def to_obj(str_x:str):
        return pickle.loads(ast.literal_eval(str_x)) # 不是从字节转成对象,是从字符串转,所以需要这样.
    

