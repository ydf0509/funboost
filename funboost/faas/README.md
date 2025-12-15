## 详细见教程4.38章节


## funboost.faas 给各种python流行web框架一键增加funboost api路由接口

`funboost.faas` 内置了对多个主流web框架的开箱即用的贡献，用户无需再亲自重复在各种python web框架中写发布消息和获取结果的的路由接口，和获取消息队列，和定时任务接口

###  funboost.faas 开箱即用  
给你自己的web服务轻松一键新增 多个 funboost 的路由接口，   

**支持的框架包括：**  
- fastapi
- flask
- django






### 使用举例
#### 举例fastapi
```
from funboost.faas import fastapi_router, CareProjectNameEnv

app = FastAPI() # app是你的fastapi app，你只需要添加这个router fastapi_router，即可一键增加多个funboost的路由接口

CareProjectNameEnv.set('test_project1') # 可选，只关注指定的test_project1项目下的队列

app.include_router(fastapi_router)
```

