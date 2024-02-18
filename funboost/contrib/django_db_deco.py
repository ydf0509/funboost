from django.db import close_old_connections


def close_old_connections_deco(f):
    """
    如果是消费函数里面需要操作django orm,那么请写上 consumin_function_decorator=close_old_connections_deco
    @boost(BoosterParams(queue_name='create_student_queue',
                         broker_kind=BrokerEnum.REDIS_ACK_ABLE,
                         consumin_function_decorator=close_old_connections_deco, # 如果gone away 一直好不了,可以加这个装饰器. django_celery django-apschrduler 这些源码中 也是调用了 close_old_connections_deco方法.

                         )
           )
    """

    def _inner(*args, **kwargs):
        close_old_connections()
        try:
            result = f(*args, **kwargs)
        finally:
            close_old_connections()

        return result

    return _inner
