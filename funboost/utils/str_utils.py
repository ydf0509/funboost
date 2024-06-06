import re


class PwdEnc:

    @classmethod
    def enc_broker_uri(cls, uri: str):
        protocol_split_list = uri.split('://')
        if len(protocol_split_list) != 2:
            return uri
        user_pass__ip_port_split_list = protocol_split_list[1].split('@')
        if len(user_pass__ip_port_split_list) != 2:
            return uri
        user__pass_split_list = user_pass__ip_port_split_list[0].split(':')
        if len(user__pass_split_list) != 2:
            return uri
        user = user__pass_split_list[0]
        pwd = user__pass_split_list[1]
        pwd_enc = cls.enc_pwd(pwd)
        return f'{protocol_split_list[0]}://{user}:{pwd_enc}@{user_pass__ip_port_split_list[1]}'

    @staticmethod
    def enc_pwd(pwd: str, plain_len=3):
        pwd_enc = pwd
        if len(pwd_enc) > plain_len:
            pwd_enc = f'{pwd_enc[:plain_len]}{"*" * (len(pwd_enc) - plain_len)}'
        return pwd_enc


class StrHelper:
    def __init__(self, strx: str):
        self.strx = strx

    def judge_contains_str_list(self, str_list: list, ignore_case=True):
        for str1 in str_list:
            if str1 in self.strx:
                return True
            if ignore_case:
                if str1.lower() in self.strx.lower():
                    return True
        return False


if __name__ == '__main__':
    str1 = "amqp://admin:abc234@108.55.33.99:5672/"
    str2 = "redis://:myRedisPass1234@127.0.0.1:6379/0"
    print(PwdEnc.enc_broker_uri(str1))
    print(PwdEnc.enc_broker_uri(str2))
    print(PwdEnc.enc_pwd('465460dsdsd'))


