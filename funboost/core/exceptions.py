

import uuid
import datetime
import time
import json

class FunboostException(Exception):
    """
    企业级通用异常基类。
    支持子类默认 message / code / error_data。
    自动生成 trace_id（可用于分布式日志）。
    """

    # 子类可覆盖以下默认项
    default_message = "An error occurred"
    default_code = None
    default_error_data = None
    enable_trace_id = False

    def __init__(self, message=None, code=None, error_data:dict=None, trace_id=None):
        # 允许实例覆盖默认字段
        self.message = message or self.default_message
        self.code = code if code is not None else self.default_code
        self.error_data = error_data if error_data is not None else self.default_error_data

        # 自动生成 trace_id
        if trace_id:
            self.trace_id = trace_id
        elif self.enable_trace_id:
            self.trace_id = str(uuid.uuid4())
        else:
            self.trace_id = None

        # super().__init__(self.message)
        super().__init__(message,code, error_data,trace_id)

    # 优雅的字符串表现形式
    def __str__(self):
        parts = [f"{self.__class__.__name__}"]  # 显示异常类型

        if self.code is not None:
            parts.append(f"[{self.code}]")

        parts.append(self.message)

        if self.error_data:
            parts.append(f"error_data={self.error_data}")

        if self.trace_id:
            parts.append(f"trace_id={self.trace_id}")

        return " | ".join(parts)

    # REPL / 日志建议信息
    def __repr__(self):
        parts = [self.__class__.__name__]

        if self.code is not None:
            parts.append(f"code={self.code}")

        parts.append(f"message={self.message!r}")

        if self.trace_id:
            parts.append(f"trace_id={self.trace_id}")

        return f"<{' '.join(parts)}>"

    # JSON 序列化
    def to_dict(self):
        # 获取当前 UTC 时间，带时区
        utc_dt = datetime.datetime.now(datetime.timezone.utc)
        utc_str = utc_dt.isoformat()  # 2025-12-10T08:30:00+00:00

        # 获取当前本地时间，带本地时区
        local_dt = utc_dt.astimezone()  # 转成本地时区
        local_str = local_dt.isoformat()  # 2025-12-10T16:30:00+08:00

        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "error_data": self.error_data,
            "trace_id": getattr(self, "trace_id", None),
            "ts": time.time(),
            "utc_time": utc_str,
            "local_time": local_str 
        }

    def to_json(self,pretty=False):
        return json.dumps(self.to_dict(),indent=4 if pretty else None,ensure_ascii=False)

    def to_fastapi_response(self, http_status=200):
        """返回fastapi的JSONResponse,让异常和fastapi的接口model保持一致，复用
        
        
        pydantic model建议明确这样写：（或者allow_extra）

        ```pyhton
        T = typing.TypeVar('T')

        class BaseResponse(BaseModel, typing.Generic[T]):
            '''
            统一的泛型响应模型
            
            字段说明:
                succ: 请求是否成功，True表示成功，False表示失败
                msg: 消息描述
                data: 返回的数据，使用泛型T
                code: 业务状态码，200表示成功，其他表示各种错误
                error: 错误类型名称（可选），如 "QueueNameNotExists", "ValueError"
                traceback: 异常堆栈信息（可选），仅在出错时返回
                trace_id: 追踪ID（可选），用于分布式追踪
            '''
            succ: bool
            msg: str
            data: typing.Optional[T] = None
            error_data: typing.Optional[typing.Dict] = None
            code: typing.Optional[int] = 200
            error: typing.Optional[str] = None
            traceback: typing.Optional[str] = None
            trace_id: typing.Optional[str] = None
        ```


        可以参考  funboost/faas/fastapi_adapter.py 的 
        register_funboost_exception_handlers 和 handle_funboost_exceptions 进行自动捕获转化。
        """


        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=http_status,
            content=self.to_dict()
        )
        # return FuncParamsError().to_fastapi_response()



class ExceptionForRetry(FunboostException):
    """为了重试的，抛出错误。只是定义了一个子类，用不用都可以，函数出任何类型错误了框架都会自动重试"""


class ExceptionForRequeue(FunboostException):
    """框架检测到此错误，重新放回当前队列中"""

class FunboostWaitRpcResultTimeout(FunboostException):
    """等待rpc结果超过了指定时间"""

class FunboostRpcResultError(FunboostException):
    """rpc结果是错误状态"""

class HasNotAsyncResult(FunboostException):
    pass

class ExceptionForPushToDlxqueue(FunboostException):
    """框架检测到ExceptionForPushToDlxqueue错误，发布到死信队列"""


class BoostDecoParamsIsOldVersion(FunboostException):
    default_message = """
你的@boost入参是老的方式,建议用新的入参方式,老入参方式不再支持函数入参代码自动补全了。

老版本的@boost装饰器方式是:
@boost('queue_name_xx',qps=3)
def f(x):
    pass
    

用户需要做的改变如下:
@boost(BoosterParams(queue_name='queue_name_xx',qps=3))
def f(x):
    pass

就是把原来函数入参的加个 BoosterParams 就可以了.

@boost这个最重要的funboost核心方法作出改变的原因是:
1/由于开发框架时候,Booster和Consumer多处需要重复声明入参,
2/入参个数较多,需要locals转化,麻烦
    """


class QueueNameNotExists(FunboostException):
    default_message = "queue name not exists"
    default_code = 4001

class FuncParamsError(FunboostException):
    default_message = "consuming function input params error"
    default_code = 5001



if __name__ == '__main__':
    try:
        raise FuncParamsError(
            'testmsg error',
            error_data={'k':'v'},
            trace_id='1234567890',
            
        )
    except FunboostException as e:
        print(e)
        print(str(e))
        print(e.to_json(pretty=True))
