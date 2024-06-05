str1 = "amqp://admin:372148@106.55.244.110:5672/"
str2 = "redis://:myRedisPass1234@127.0.0.1:6379/0"


# user_pass, rest = str1.split('://')[1].split('@')
# print(user_pass, rest)
# user, password = user_pass.split(':')
# print(user,password)

def enc_broker_uri(uri: str):
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
    pwd_enc = enc_pwd(pwd)
    return f'{protocol_split_list[0]}://{user}:{pwd_enc}@{user_pass__ip_port_split_list[1]}'


def enc_pwd(pwd: str):
    pwd_enc = pwd
    if len(pwd_enc) > 3:
        pwd_enc = f'{pwd_enc[:3]}{"*" * (len(pwd_enc) - 3)}'
    return pwd_enc


if __name__ == '__main__':
    print(enc_broker_uri(str1))
    print(enc_broker_uri(str2))
