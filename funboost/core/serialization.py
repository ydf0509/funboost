import typing

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


class PickleHelper:
    @staticmethod
    def to_str(obj_x):
        return str(pickle.dumps(obj_x))
    
    @staticmethod
    def to_obj(str_x):
        return pickle.loads(ast.literal_eval(str_x))
    

    