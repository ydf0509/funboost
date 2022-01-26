import inspect
import nb_log
from funboost import boost
from funboost.utils import RedisMixin
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


@boost('test_queue_235',consumin_function_decorator=incr_deco(f'run_count:{nb_log.nb_log_config_default.computer_ip}'),
       do_task_filtering=True)
# @incr_deco('test_queue_235_run_count')
def fun(xxx, yyy):
    print(xxx + yyy)
    return xxx + yyy


if __name__ == '__main__':
    print(inspect.getfullargspec(fun))

    for i in range(20):
        fun.push(i, 2 * i)
    fun.multi_process_consume(2)
