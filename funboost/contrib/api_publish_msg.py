import traceback

from funboost import AioAsyncResult, AsyncResult

from funboost.core.cli.discovery_boosters import BoosterDiscovery
from funboost import BoostersManager
from fastapi import FastAPI
from pydantic import BaseModel


class MsgItem(BaseModel):
    queue_name: str  # 队列名
    msg_body: dict  # 消息体,就是boost函数的入参字典,例如 {"x":1,"y":2}
    need_result: bool = False  # 发布消息后,是否需要返回结果
    timeout: int = 60  # 等待结果返回的最大等待时间.


class PublishResponse(BaseModel):
    succ: bool
    msg: str
    status_and_result: dict = None  # 消费函数的消费状态和结果.


# 创建 FastAPI 应用实例
app = FastAPI()

'''
如果你在发布消息后还需要获取函数执行结果,
那么推荐使用asyncio类型的web框架例如 fastapi tornado,而不是使用flask django,更好的应付由于获取结果而需要的阻塞时间.不使用asyncio的话web框架需要设置开启很高的线程才行.
'''


@app.post("/funboost_publish_msg")
async def publish_msg(msg_item: MsgItem):
    status_and_result = None
    try:
        booster = BoostersManager.get_or_create_booster_by_queue_name(msg_item.queue_name)
        if msg_item.need_result:
            if booster.boost_params['is_using_rpc_mode'] is False:
                raise ValueError(f' need_result 为true,{booster.queue_name} 队列消费者 需要@boost设置支持rpc模式')
            async_result = booster.publish(msg_item.msg_body)
            status_and_result = await AioAsyncResult(async_result.task_id, timeout=msg_item.timeout).status_and_result
            # status_and_result = AsyncResult(async_result.task_id, timeout=msg_item.timeout).status_and_result
        else:
            booster.publish(msg_item.msg_body)
        return PublishResponse(succ=True, msg=f'{msg_item.queue_name} 队列,消息发布成功', status_and_result=status_and_result)
    except Exception as e:
        return PublishResponse(succ=False, msg=f'{msg_item.queue_name} 队列,消息发布失败 {type(e)} {e} {traceback.format_exc()}',
                               status_and_result=status_and_result)


# 运行应用
if __name__ == "__main__":
    import uvicorn

    uvicorn.run('funboost.contrib.api_publish_msg:app', host="0.0.0.0", port=16666, workers=4)

    '''
    test_frame/test_api_publish_msg 中有使用例子.
    '''
