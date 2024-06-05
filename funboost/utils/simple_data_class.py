import json

import copy
import typing

from funboost.utils import json_helper
from funboost.utils.str_utils import PwdEnc, StrHelper


class DataClassBase:
    """
    使用类实现的 简单数据类。
    也可以使用装饰器来实现数据类
    """

    def __new__(cls, **kwargs):
        self = super().__new__(cls)
        self.__dict__ = copy.copy({k: v for k, v in cls.__dict__.items() if not k.startswith('__')})
        return self

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __call__(self, ) -> dict:
        return self.get_dict()

    def get_dict(self):
        return {k: v.get_dict() if isinstance(v, DataClassBase) else v for k, v in self.__dict__.items()}

    def __str__(self):
        return f"{self.__class__}    {self.get_dict()}"

    def __getitem__(self, item):
        return getattr(self, item)

    def get_json(self,indent=4):
        return json_helper.dict_to_un_strict_json(self.get_dict(),indent=indent)

    def get_pwd_enc_json(self,indent=4):
        """防止打印密码明文,泄漏密码"""
        dict_new = {}
        for k, v in self.get_dict().items():
            # only_print_on_main_process(f'{k} :  {v}')
            if isinstance(v, (bool, tuple, dict, float, int)):
                dict_new[k] = v
            else:
                v_enc =PwdEnc.enc_broker_uri(str(v))
                if StrHelper(k).judge_contains_str_list(['pwd', 'pass_word', 'password', 'passwd', 'pass']):
                    v_enc = PwdEnc.enc_pwd(v_enc)
                dict_new[k] = v_enc
        return json.dumps(dict_new, ensure_ascii=False, indent=indent)

    @classmethod
    def update_cls_attribute(cls,**kwargs):
        for k ,v in kwargs.items():
            setattr(cls,k,v)
        return cls

    def update_instance_attribute(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self


if __name__ == '__main__':
    import datetime


    class A(DataClassBase):
        x = 1
        y = 2
        z = datetime.datetime.now()


    print(A())
    print(A(y=3))
    print(A(y=5).get_dict())

    print(A()['y'])
    print(A().y)
