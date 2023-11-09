import requests
from funboost.concurrent_pool.custom_threadpool_executor import ThreadPoolExecutorShrinkAble


def req_push1(i):
    resp = requests.post('http://127.0.0.1:16667/funboost_publish_msg',
                         json={'queue_name': 'task_api_push_queue1',
                               'msg_body': {"x": 1 * i, "y": 2 * i},
                               'need_result': True, 'timeout': 10})

    print(resp.text)


def req_push2(i):
    resp = requests.post('http://127.0.0.1:16667/funboost_publish_msg',
                         json={'queue_name': 'task_api_push_queue2',
                               'msg_body': {"a": 1 * i, "b": 2 * i},
                               'need_result': False, 'timeout': 10})

    print(resp.text)


pool = ThreadPoolExecutorShrinkAble(10)
for j in range(1000):
    pool.submit(req_push1, j)
    pool.submit(req_push2, j)
