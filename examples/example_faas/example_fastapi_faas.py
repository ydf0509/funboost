"""
此模块演示用户如果使用了fastapi，如何轻松一键新增 多个 funbost 的路由接口，
包括 /funboost/publish 和 /funboost/get_result 和 /funboost/get_msg_count 等几十个接口
这样用户就可以避免需要亲自写funboost发布消息和获取结果的的fastapi路由接口


from funboost.faas import fastapi_router
app.include_router(fastapi_router) # 只需要这样，你的fastapi app即可新增多个 funbost 的路由接口
"""


import uvicorn
from fastapi import FastAPI

from funboost.faas import fastapi_router,CareProjectNameEnv 


CareProjectNameEnv.set('test_project1') # 可选，只关注指定的test_project1项目下的队列，减少无关队列的干扰。

# Create FastAPI app
app = FastAPI()

@app.get('/')
async def index():
    return "Hello World"

# 2. Include funboost.faas fastapi_router
app.include_router(fastapi_router)  # 这是核心用法


# 4. Run the app
if __name__ == '__main__':
    # The consumer runs in the background threads/processes started by @boost.
    # We run uvicorn to serve the API.
    print("Starting FastAPI app with Funboost Router...")
    
    print("启动 Funboost API 服务...")
    print("接口文档: http://127.0.0.1:8000/docs")
    print("Try POST http://127.0.0.1:8000/funboost/publish with body: {'queue_name': 'test_funboost_faas_queue', 'msg_body': {'x': 1, 'y': 2}, 'need_result': true}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
