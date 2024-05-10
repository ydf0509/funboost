from fastapi import FastAPI
from funboost import AioAsyncResult

from consume_fun import aio_long_time_fun, long_time_fun

app = FastAPI()


@app.get("/")
async def root():
    return {"Hello": "World"}


# 演示push同步发布, 并且aio rpc获取消费结果
@app.get("/url1/{name}")
async def api1(name: str):
    async_result = long_time_fun.push(name)  # 通常发布消息时间比较小,局域网内一般少于0.3毫秒,所以在asyncio的异步方法中调用同步io方法一般不会产生过于严重的灾难
    return {"result": await AioAsyncResult(async_result.task_id).result}   # 一般情况下不需要请求时候立即使用rpc模式获取消费结果,直接吧消息发到中间件后就不用管了.前端使用ajx轮训或者mqtt
    # return {"result": async_result.result}  # 如果你直接这样写代码,会产生所有协程全局阻塞灭顶之灾.

# 演示aio_push 异步发布, 并且aio rpc获取消费结果
@app.get("/url2/{name}")
async def api2(name: str):
    asio_async_result = await aio_long_time_fun.aio_push(name)  # 如果你用的是asyncio编程生态,那还是建议这种,尤其是对外网发布消息会耗时大的情况下.
    return {"result": await asio_async_result.result}  # 一般情况下不需要请求时候立即使用rpc模式获取消费结果,直接吧消息发到中间件后就不用管了.前端使用ajx轮训或者mqtt


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)