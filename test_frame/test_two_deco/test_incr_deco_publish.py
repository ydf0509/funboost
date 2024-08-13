import inspect
import nb_log
from funboost import BoosterParams
from funboost.utils.redis_manager import RedisMixin
from functools import wraps


def incr_deco(redis_key):
    def _inner(f):
        @wraps(f)
        def __inner(*args, **kwargs):
            result = f(*args, **kwargs)
            RedisMixin().redis_db_frame.incr(redis_key)
            # 创建索引

            # MongoMixin().mongo_client.get_database('basea').get_collection('cola').insert({'result':result,'args':str(args),'kwargs':str(kwargs)})
            return result

        return __inner

    return _inner


@BoosterParams(queue_name='test_queue_23b',
               should_check_publish_func_params=False,  # 这一行很重要，should_check_publish_func_params必须设置为False，如果你是直接把装饰器加到函数上了，funboost无法获取函数的入参名字，无法自动生成json消息，所以需要用户自己publish来发布入参字典。
               )
@incr_deco('test_queue_23b_run_count')
def fun(xxx, yyy):
    print(xxx + yyy)
    return xxx + yyy


if __name__ == '__main__':

    for i in range(20):
        # fun.push(i, 2 * i) # 不可以fun.push这样发布
        fun.publish({'xxx': 1, 'yyy': 2})  # 直接把装饰器写在消费函数上，那就用户需要使用publish发布，且boost装饰器设置should_check_publish_func_params=False
    fun.consume()
