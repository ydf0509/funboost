import re


class PwdEnc:

    @classmethod
    def enc_broker_uri(cls, uri: str):
        """
        对连接字符串中的密码进行脱敏处理
        
        支持两种格式：
        1. URI 格式: protocol://user:password@host:port
        2. libpq DSN 格式: host=xxx port=xxx password=xxx
        """
        # 尝试处理 libpq DSN 格式（如 PostgreSQL 的 password=xxx）
        if 'password=' in uri.lower():
            return cls._enc_libpq_dsn(uri)
        
        # 处理标准 URI 格式
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

    @classmethod
    def _enc_libpq_dsn(cls, dsn: str):
        """
        处理 libpq DSN 格式的密码脱敏
        例如: host=xxx port=xxx password=secret123 -> host=xxx port=xxx password=sec*******
        """
        # 使用正则匹配 password=xxx 格式（支持带引号和不带引号）
        pattern = r'(password\s*=\s*)([\'"]?)([^\s\'"]+)([\'"]?)'
        
        def replace_pwd(match):
            prefix = match.group(1)  # password=
            quote_start = match.group(2)  # 可能的引号
            pwd = match.group(3)  # 密码值
            quote_end = match.group(4)  # 可能的引号
            pwd_enc = cls.enc_pwd(pwd)
            return f'{prefix}{quote_start}{pwd_enc}{quote_end}'
        
        return re.sub(pattern, replace_pwd, dsn, flags=re.IGNORECASE)

    @staticmethod
    def enc_pwd(pwd: str, hide_prefix=3, hide_suffix=3):
        """
        密码脱敏：前N位隐藏为***，后N位隐藏为***，中间显示
        例如: abc12345def -> ***12345***
        """
        if len(pwd) <= hide_prefix + hide_suffix:
            return '***'  # 太短则全部隐藏
        middle = pwd[hide_prefix:-hide_suffix] if hide_suffix > 0 else pwd[hide_prefix:]
        return f'***{middle}***'


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
    # 测试 URI 格式
    str1 = "amqp://admin:abc234@108.55.33.99:5672/"
    str2 = "redis://:myRedisPass1234@127.0.0.1:6379/0"
    print("URI 格式测试:")
    print(f"  {str1} -> {PwdEnc.enc_broker_uri(str1)}")
    print(f"  {str2} -> {PwdEnc.enc_broker_uri(str2)}")
    
    # 测试 libpq DSN 格式
    str3 = "host=106.55.244.110 port=5432 dbname=testdb user=postgres password=postgres123"
    str4 = "dbname='mydb' user='admin' password='secret456' host='localhost'"
    print("\nlibpq DSN 格式测试:")
    print(f"  {str3}")
    print(f"  -> {PwdEnc.enc_broker_uri(str3)}")
    print(f"  {str4}")
    print(f"  -> {PwdEnc.enc_broker_uri(str4)}")
    
    # 测试密码加密
    print(f"\n密码加密测试: 465460dsdsd -> {PwdEnc.enc_pwd('465460dsdsd')}")
