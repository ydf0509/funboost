import copy


def get_publish_time(paramsx: dict):
    """
    :param paramsx:
    :return:
    """
    return paramsx.get('extra', {}).get('publish_time', None)


def _delete_keys_and_return_new_dict(dictx: dict, keys: list = None):
    dict_new = copy.copy(dictx)  # 主要是去掉一级键 publish_time，浅拷贝即可。新的消息已经不是这样了。
    keys = ['publish_time', 'publish_time_format', 'extra'] if keys is None else keys
    for dict_key in keys:
        try:
            dict_new.pop(dict_key)
        except KeyError:
            pass
    return dict_new