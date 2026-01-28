
"""
fastapi 开箱即用，只需要用户的 app.include_router(fastapi_router) ,即可自动给用户的fastapi添加常用路由，实现faas




使用说明:
    在用户自己的 FastAPI 项目中
       app.include_router(fastapi_router)
    


如果fastapi_router集成到你自己的fastapi app时候，你觉得需要加上权限鉴权，可以这样： 
app.include_router(
    fastapi_router,
    dependencies=[
        Depends(your_authenticate),
    ]
)

"""

import traceback
import typing
import asyncio

from funboost import AioAsyncResult, AsyncResult, TaskOptions, BoosterParams, Booster

from funboost.core.active_cousumer_info_getter import SingleQueueConusmerParamsGetter, QueuesConusmerParamsGetter,CareProjectNameEnv
from funboost.core.exceptions import FunboostException
from fastapi import FastAPI, APIRouter, Query, Request, Response
from fastapi.responses import JSONResponse


try:
    from pydantic import BaseModel, ConfigDict  # v2
    pydantic_version = 'v2'
except ImportError:
    from pydantic import BaseModel              # v1
    ConfigDict = None
    pydantic_version = 'v1'
from funboost.core.loggers import get_funboost_file_logger
from funboost.utils.redis_manager import RedisMixin
from funboost.constant import RedisKeys
from funboost.faas.faas_util import gen_aps_job_adder

logger = get_funboost_file_logger(__name__)





# 创建 Router 实例，方便用户 include 到自己的 app 中
# 用户可以使用 app.include_router(fastapi_router)
fastapi_router = APIRouter(prefix='/funboost', tags=['funboost'])





# ==================== fastapi app 处理装饰器 ====================
# 会影响用户自己的 app，看用户自己喜好了，因为有的用户的response是自定义的，不是funboost fatapi_router的BaseResponse。

async def funboost_exception_handler(request: Request, exc: FunboostException) -> JSONResponse:
    """
    统一处理 FunboostException 类型的异常
    自动提取异常的 code、message、data 等信息返回给前端
    """
    # 注意：这里不能直接返回 BaseResponse，因为FastAPI的异常处理器需要返回Response对象
    # 但我们可以使用BaseResponse的结构来保持格式一致
    response_data = {
        "succ": False,
        "msg": exc.message,
        "code": exc.code or 5000,
        "error_data": exc.error_data,
        "error": exc.__class__.__name__,
        "traceback": None,  # FunboostException不返回traceback
        "trace_id": getattr(exc, "trace_id", None)
    }
    return JSONResponse(
        status_code=200,  # HTTP状态码仍然返回200,业务错误通过code区分
        content=response_data
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    统一处理所有其他异常
    返回固定code 5555,并包含完整的异常堆栈信息
    """
    logger.exception(f'未预期的异常: {str(exc)}')
    response_data = {
        "succ": False,
        "msg": f"系统错误: {type(exc).__name__}: {str(exc)}",
        "code": 5555,
        "error_data": None,
        "error": type(exc).__name__,
        "traceback": traceback.format_exc(),
        "trace_id": None
    }
    return JSONResponse(
        status_code=200,  # HTTP状态码仍然返回200,业务错误通过code区分
        content=response_data
    )


def register_funboost_exception_handlers(app: FastAPI):
    """
    注册 Funboost 的全局异常处理器到 FastAPI app
    
    使用示例:
        from funboost.faas.fastapi_adapter import fastapi_router, register_funboost_exception_handlers
        
        app = FastAPI()
        app.include_router(fastapi_router)
        register_funboost_exception_handlers(app)  # 注册全局异常处理
    """
    app.add_exception_handler(FunboostException, funboost_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)




# ==================== Funboost Router 异常处理装饰器 ====================
# 只针对 funboost router 的接口，不影响用户自己的 app

def handle_funboost_exceptions(func):
    """
    装饰器：统一处理 funboost router 接口的异常
    只在 funboost 的接口中使用，不会影响用户自己的 FastAPI app
    
    使用方法:
        @fastapi_router.get("/some_endpoint")
        @handle_funboost_exceptions
        async def some_endpoint():
            # 直接写业务逻辑，不需要 try-except
            return BaseResponse(...)
    
    异常处理规则:
        - FunboostException: 返回异常的 code、message、data、trace_id
        - 其他异常: 返回 code 5555，包含完整堆栈信息
    """
    import functools
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            # 如果是异步函数
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except FunboostException as e:
            # 处理 FunboostException
            # print(4444,e.to_dict())
            return BaseResponse(
                succ=False,
                msg=e.message,
                code=e.code or 5000,
                error_data=e.error_data,
                error=e.__class__.__name__,
                traceback=traceback.format_exc(),  
                trace_id=getattr(e, "trace_id", None)
            )
        except Exception as e:
            # 处理其他异常
            logger.exception(f'未预期的异常: {str(e)}')
            return BaseResponse(
                succ=False,
                msg=f"系统错误: {type(e).__name__}: {str(e)}",
                code=5555,
                error_data=None,
                error=type(e).__name__,
                traceback=traceback.format_exc(),
                trace_id=None
            )
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FunboostException as e:
            # 处理 FunboostException
            # print(4444,e.to_dict())
            return BaseResponse(
                succ=False,
                msg=e.message,
                code=e.code or 5000,
                error_data=e.error_data,
                error=e.__class__.__name__,
                traceback=traceback.format_exc(),  
                trace_id=getattr(e, "trace_id", None)
            )
        except Exception as e:
            # 处理其他异常
            logger.exception(f'未预期的异常: {str(e)}')
            return BaseResponse(
                succ=False,
                msg=f"系统错误: {type(e).__name__}: {str(e)}",
                code=5555,
                error_data=None,
                error=type(e).__name__,
                traceback=traceback.format_exc(),
                trace_id=None
            )
    
    # 根据函数类型返回对应的包装器
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper



class BaseAllowExtraModel(BaseModel):
    
    if pydantic_version == 'v2':
        # Pydantic v2 使用
        model_config = ConfigDict(extra="allow")

    elif pydantic_version == 'v1':
        # Pydantic v1 使用
        class Config:
            extra = "allow"



# 统一响应模型（泛型）
T = typing.TypeVar('T')

class BaseResponse(BaseModel, typing.Generic[T]):
    """
    统一的泛型响应模型
    
    字段说明:
        succ: 请求是否成功，True表示成功，False表示失败
        msg: 消息描述
        data: 返回的数据，使用泛型T
        code: 业务状态码，200表示成功，其他表示各种错误
        error: 错误类型名称（可选），如 "QueueNameNotExists", "ValueError"
        traceback: 异常堆栈信息（可选），仅在出错时返回
        trace_id: 追踪ID（可选），用于分布式追踪
    """
    succ: bool
    msg: str
    data: typing.Optional[T] = None
    error_data: typing.Optional[typing.Dict] = None
    code: typing.Optional[int] = 200
    error: typing.Optional[str] = None
    traceback: typing.Optional[str] = None
    trace_id: typing.Optional[str] = None


class MsgItem(BaseModel):
    queue_name: str  # 队列名
    msg_body: dict  # 消息体,就是boost函数的入参字典,例如 {"x":1,"y":2}
    need_result: bool = False  # 发布消息后,是否需要返回结果
    timeout: int = 60  # 等待结果返回的最大等待时间.
    task_id: str = None  # 可选：指定 task_id


# 统一响应格式的数据结构

# 函数执行结果状态的详细模型（参考 FunctionResultStatus）
class FunctionResultStatusModel(BaseModel):
    """
    函数执行结果状态模型
    对应 FunctionResultStatus.get_status_dict() 的返回值结构
    """
    # 基本信息
    host_process: str  # 主机名-进程ID，例如 "LAPTOP-7V78BBO2 - 34572"
    queue_name: str  # 队列名称
    function: str  # 函数名称
    
    # 消息信息
    msg_dict: dict  # 原始消息字典
    task_id: str  # 任务ID
    
    # 进程和线程信息
    process_id: int  # 进程ID
    thread_id: int  # 线程ID
    total_thread: int  # 活跃线程总数
    
    # 时间信息
    publish_time: float  # 发布时间（时间戳）
    publish_time_format: str  # 发布时间格式化字符串，例如 "2025-12-05 13:28:12"
    time_start: float  # 开始执行时间（时间戳）
    time_cost: typing.Optional[float]  # 执行耗时（秒）
    time_end: float  # 结束时间（时间戳）
    insert_time_str: str  # 插入时间字符串，例如 "2025-12-05 13:28:13"
    insert_minutes: str  # 插入时间精确到分钟，例如 "2025-12-05 13:28"
    
    # 参数信息
    params: dict  # 函数参数（字典形式）
    params_str: str  # 函数参数（JSON字符串形式）
    
    # 执行结果信息
    result: typing.Any  # 函数执行结果
    run_times: int  # 运行次数
    success: bool  # 是否成功
    run_status: str  # 运行状态：'running' 或 'finish'
    
    # 异常信息（可选）
    exception: typing.Optional[str]  # 异常详情
    exception_type: typing.Optional[str]  # 异常类型
    exception_msg: typing.Optional[str]  # 异常消息
    rpc_chain_error_msg_dict: typing.Optional[dict]  # RPC链式调用错误信息
    
    # RPC配置
    rpc_result_expire_seconds: typing.Optional[int]  # RPC结果过期时间（秒）
    
    # 主机信息
    host_name: str  # 主机名，例如 "LAPTOP-7V78BBO2"
    script_name: str  # 脚本名称（短），例如 "example_fastapi_router.py"
    script_name_long: str  # 脚本名称（完整路径）

    user_context: typing.Optional[dict] = {}  # 用户自定义的额外信息，用户随意存放任何信息。
    
    # MongoDB文档ID
    _id: str  # MongoDB 文档ID，通常等于 task_id
    
    class Config:
        # 允许字段别名（如 _id）
        populate_by_name = True


class RpcRespData(BaseAllowExtraModel):
    task_id: typing.Optional[str] = None
    status_and_result: typing.Optional[FunctionResultStatusModel] = None  # 消费函数的消费状态和结果


class CountData(BaseModel):
    queue_name: str
    count: int = -1


class AllQueuesData(BaseModel):
    queues: typing.List[str] = []
    count: int = 0


class DeprecateQueueRequest(BaseModel):
    """废弃队列请求模型"""
    queue_name: str  # 要废弃的队列名称


class DeprecateQueueData(BaseModel):
    """废弃队列响应数据模型"""
    queue_name: str
    removed: bool  # 是否成功移除


@fastapi_router.post("/publish", response_model=BaseResponse[RpcRespData])
async def publish_msg(msg_item: MsgItem):
    """
    发布消息接口，支持RPC模式。
    支持queue_name是否存在的校验，支持校验消息内容是否正确。所以不用担心跨部门用户使用了错误的queue_name，或者消息内容不正确。

    用户可以先通过 /get_queues_config 接口获取所有队列的配置信息，就知道有哪些队列，以及每个队列支持的消费函数的消息内容需要包括哪些入参字段了。
    # 发布消息时候会立即校验入参是否正确，使用了redis中的 booster配置的 auto_generate_info.final_func_input_params_info 信息来校验入参名字和个数是否正确
    """
    status_and_result = None
    task_id = None
    try:
        # SingleQueueConusmerParamsGetter(msg_item.queue_name).gen_publisher_for_faas() 从 funboost 的reids配置中生成 publisher
        # 不需要用户亲自判断queue_name，然后精确使用某个非常具体的消费函数，


        publisher = SingleQueueConusmerParamsGetter(msg_item.queue_name).gen_publisher_for_faas()
        booster_params_by_redis = SingleQueueConusmerParamsGetter(msg_item.queue_name).get_one_queue_params_use_cache()
        
        # 检查是否需要 RPC 模式
        if msg_item.need_result:
          
            # 开启 RPC 模式发布
            async_result = await publisher.aio_publish(
                msg_item.msg_body,
                task_id=msg_item.task_id,  # 可选：指定 task_id（用于重试失败任务）
                task_options=TaskOptions(is_using_rpc_mode=True)
            )
            task_id = async_result.task_id
            # 等待结果
            status_and_result = await AioAsyncResult(async_result.task_id, timeout=msg_item.timeout).status_and_result
        else:
            # 普通发布，可以指定 task_id
            async_result = await publisher.aio_publish(msg_item.msg_body, task_id=msg_item.task_id)
            task_id = async_result.task_id

        return BaseResponse[RpcRespData](
            succ=True,
            msg=f'{msg_item.queue_name} 队列,消息发布成功',
            data=RpcRespData(
                task_id=task_id,
                status_and_result=status_and_result
            )
        )
    except Exception as e:
        logger.exception(f'发布消息失败: {str(e)}')
        return BaseResponse[RpcRespData](
            succ=False,
            msg=f'{msg_item.queue_name} 队列,消息发布失败 {type(e)} {e} {traceback.format_exc()}',
            data=RpcRespData(
                task_id=task_id,
                status_and_result=status_and_result
            )
        )


@fastapi_router.get("/get_result", response_model=BaseResponse[RpcRespData])
async def get_result(task_id: str, timeout: int = 5,):
    """
    根据 task_id 获取任务执行结果
    """
    try:
        # 尝试获取结果，默认给个短的 timeout 防止一直阻塞，或者复用 AioAsyncResult 的逻辑
        # 注意：如果任务还在运行，AioAsyncResult 会阻塞直到 timeout
        # 如果任务早已完成并过期，这里可能返回 None
        status_and_result = await AioAsyncResult(task_id, timeout=timeout).status_and_result
        
        if status_and_result:
            return BaseResponse[RpcRespData](
                succ=True,
                msg="获取成功",
                data=RpcRespData(
                    task_id=task_id,
                    status_and_result=status_and_result
                )
            )
        else:
            return BaseResponse[RpcRespData](
                succ=False,
                msg="未获取到结果(可能已过期或未开始执行或超时或压根没启动消费)",
                data=RpcRespData(
                    task_id=task_id,
                    status_and_result=None
                )
            )
            
    except Exception as e:
        logger.exception(f'获取结果失败: {str(e)}')
        return BaseResponse[RpcRespData](
            succ=False,
            msg=f"获取结果出错: {str(e)}",
            data=RpcRespData(
                task_id=task_id,
                status_and_result=None
            )
        )


# 队列控制接口（暂停/恢复）

class QueueNameRequest(BaseModel):
    """队列名称请求模型"""
    queue_name: str


class QueueControlData(BaseModel):
    """队列控制操作的响应数据"""
    queue_name: str
    success: bool


@fastapi_router.post("/pause_consume", response_model=BaseResponse[QueueControlData])
def pause_consume(request: QueueNameRequest):
    """
    暂停队列消费
    
    请求体:
        {
            "queue_name": "队列名称"
        }
    
    返回:
        暂停操作的结果
        
    说明:
        此接口会在 Redis 中设置暂停标志为 '1'，消费者会定期检查此标志并暂停消费。
        暂停不会立即生效，需要等待消费者检查标志的时间间隔。
    """
    try:
        
        
        RedisMixin().redis_db_frame.hset(RedisKeys.REDIS_KEY_PAUSE_FLAG, request.queue_name, '1')
        
        return BaseResponse[QueueControlData](
            succ=True,
            msg=f"队列 {request.queue_name} 暂停成功",
            data=QueueControlData(
                queue_name=request.queue_name,
                success=True
            )
        )
    except Exception as e:
        logger.exception(f'暂停队列消费失败: {str(e)}')
        return BaseResponse[QueueControlData](
            succ=False,
            msg=f"暂停队列 {request.queue_name} 失败: {str(e)}",
            data=QueueControlData(
                queue_name=request.queue_name,
                success=False
            )
        )


@fastapi_router.post("/resume_consume", response_model=BaseResponse[QueueControlData])
def resume_consume(request: QueueNameRequest):
    """
    恢复队列消费
    
    请求体:
        {
            "queue_name": "队列名称"
        }
    
    返回:
        恢复操作的结果
        
    说明:
        此接口会在 Redis 中设置暂停标志为 '0'，消费者会定期检查此标志并恢复消费。
        恢复不会立即生效，需要等待消费者检查标志的时间间隔。
    """
    try:
        
        
        RedisMixin().redis_db_frame.hset(RedisKeys.REDIS_KEY_PAUSE_FLAG, request.queue_name, '0')
        
        return BaseResponse[QueueControlData](
            succ=True,
            msg=f"队列 {request.queue_name} 恢复成功",
            data=QueueControlData(
                queue_name=request.queue_name,
                success=True
            )
        )
    except Exception as e:
        logger.exception(f'恢复队列消费失败: {str(e)}')
        return BaseResponse[QueueControlData](
            succ=False,
            msg=f"恢复队列 {request.queue_name} 失败: {str(e)}",
            data=QueueControlData(
                queue_name=request.queue_name,
                success=False
            )
        )



@fastapi_router.get("/get_msg_count", response_model=BaseResponse[CountData])
@handle_funboost_exceptions  # 使用装饰器统一处理异常，不影响用户的app
def get_msg_count(queue_name: str):
    """
    根据 queue_name 获取消息数量
    
    注意：此接口使用了 @handle_funboost_exceptions 装饰器
    所以不需要写 try-except，异常会自动被捕获并返回统一格式
    """
    # 直接写业务逻辑，不需要 try-except
    publisher = SingleQueueConusmerParamsGetter(queue_name).gen_publisher_for_faas()
    # 获取消息数量（注意：某些中间件可能不支持准确计数，返回-1）
    count = publisher.get_message_count()
    return BaseResponse[CountData](
        succ=True,
        msg="获取成功",
        data=CountData(
            queue_name=queue_name,
            count=count
        )
    )
# 队列清空接口

class ClearQueueData(BaseModel):
    """清空队列响应数据"""
    queue_name: str
    success: bool


@fastapi_router.post("/clear_queue", response_model=BaseResponse[ClearQueueData])
def clear_queue(request: QueueNameRequest):
    """
    清空队列中的所有消息
    
    请求体:
        {
            "queue_name": "队列名称"
        }
    
    返回:
        清空操作的结果
        
    说明:
        此接口会清空指定队列中的所有待消费消息。
        ⚠️ 此操作不可逆，请谨慎使用！
        
    注意:
        broker_kind 会自动从已注册的 booster 中获取，无需手动指定。
    """
    try:
        # 通过 queue_name 自动获取对应的 booster
        publisher = SingleQueueConusmerParamsGetter(request.queue_name).gen_publisher_for_faas()
        publisher.clear()
        
        return BaseResponse[ClearQueueData](
            succ=True,
            msg=f"队列 {request.queue_name} 清空成功",
            data=ClearQueueData(
                queue_name=request.queue_name,
                success=True
            )
        )
    except Exception as e:
        logger.exception(f'清空队列失败: {str(e)}')
        return BaseResponse[ClearQueueData](
            succ=False,
            msg=f"清空队列 {request.queue_name} 失败: {str(e)}",
            data=ClearQueueData(
                queue_name=request.queue_name,
                success=False
            )
        )




@fastapi_router.get("/get_all_queues", response_model=BaseResponse[AllQueuesData])
def get_all_queues():
    """
    获取所有已注册的队列名称
    
    返回所有通过 @boost 装饰器注册的队列名称列表
    """
    try:
        # 获取所有队列名称
        all_queues = QueuesConusmerParamsGetter().get_all_queue_names()
        
        return BaseResponse[AllQueuesData](
            succ=True,
            msg="获取成功",
            data=AllQueuesData(
                queues=all_queues,
                count=len(all_queues)
            )
        )
    except Exception as e:
        logger.exception(f'获取所有队列失败: {str(e)}')
        return BaseResponse[AllQueuesData](
            succ=False,
            msg=f"获取所有队列失败: {str(e)}",
            data=AllQueuesData(
                queues=[],
                count=0
            )
        )




# 队列配置参数详细模型（参考 BoosterParams）
class QueueParams(BaseAllowExtraModel):
    """
    队列的完整配置参数，
    和BoosterParams不同的是，这里是完全版可json序列化的
    这里的数据是从redis获取的，redis只能存json序列化的数据。
    
    """
    # 基础配置
    queue_name: str  # 队列名字
    broker_kind: str  # 中间件类型，如 REDIS, RABBITMQ 等
    project_name: typing.Optional[str] = None # 项目名
    
    # 并发配置
    concurrent_mode: str  # 并发模式：threading/gevent/eventlet/async/single_thread
    concurrent_num: int  # 并发数量
    specify_concurrent_pool: typing.Optional[typing.Any]  # 指定的线程池/协程池
    specify_async_loop: typing.Optional[typing.Any]   # 指定的async loop
    is_auto_start_specify_async_loop_in_child_thread: bool  # 是否自动在子线程启动async loop
    
    # 频率控制
    qps: typing.Optional[float]  # QPS限制（每秒执行次数）
    is_using_distributed_frequency_control: bool  # 是否使用分布式频控
    
    # 心跳与监控
    is_send_consumer_heartbeat_to_redis: bool  # 是否发送消费者心跳到redis
    
    # 重试配置
    max_retry_times: int  # 最大自动重试次数
    retry_interval: typing.Union[float, int]  # 重试间隔（秒）
    is_push_to_dlx_queue_when_retry_max_times: bool  # 达到最大重试次数后是否推送到死信队列
    
    # 函数装饰与超时
    consuming_function_decorator: typing.Optional[typing.Any]    # 函数装饰器
    function_timeout: typing.Optional[float]  # 函数超时时间（秒）
    is_support_remote_kill_task: bool  # 是否支持远程杀死任务
    
    # 日志配置
    log_level: int  # 日志级别
    logger_prefix: str  # 日志名字前缀
    create_logger_file: bool  # 是否创建文件日志
    logger_name: str  # 日志命名空间
    log_filename: typing.Optional[str]  # 日志文件名
    is_show_message_get_from_broker: bool  # 是否显示从broker获取的消息
    is_print_detail_exception: bool  # 是否打印详细异常堆栈
    publish_msg_log_use_full_msg: bool  # 发布消息日志是否显示完整消息
    
    # 消息过期与过滤
    msg_expire_seconds: typing.Optional[float]  # 消息过期时间（秒）
    do_task_filtering: bool  # 是否对函数入参进行过滤去重
    task_filtering_expire_seconds: int  # 任务过滤的失效期
    
    # 函数结果持久化
    function_result_status_persistance_conf: typing.Dict[str, typing.Any]  # 函数结果状态持久化配置
    
    # 用户自定义
    user_custom_record_process_info_func: typing.Optional[typing.Any]  # 用户自定义的保存消息处理记录函数
    
    # RPC模式
    is_using_rpc_mode: bool  # 是否使用RPC模式
    rpc_result_expire_seconds: int  # RPC结果过期时间（秒）
    rpc_timeout: int  # RPC超时时间（秒）
    
    # 延时任务
    delay_task_apscheduler_jobstores_kind: str  # 延时任务的jobstore类型：redis/memory
    
    # 定时运行控制
    is_do_not_run_by_specify_time_effect: bool  # 是否使不运行的时间段生效
    do_not_run_by_specify_time: typing.Tuple[str, str]  # 不运行的时间段
    
    # 启动控制
    schedule_tasks_on_main_thread: bool  # 是否在主线程调度任务
    is_auto_start_consuming_message: bool  # 是否自动启动消费
    
    # 分组管理
    booster_group: typing.Optional[str]  # 消费分组名字
    
    # 消费函数信息
    consuming_function: typing.Any  # 消费函数
    consuming_function_raw: typing.Any  # 原始消费函数
    consuming_function_name: str  # 消费函数名称
    
    # 中间件专属配置
    broker_exclusive_config: typing.Dict[str, typing.Any]  # 不同中间件的专属配置
    
    # 参数校验
    should_check_publish_func_params: bool  # 是否校验发布时的函数参数
    manual_func_input_params :typing.Optional[typing.Dict[str, typing.Any]] = None # 手动指定函数入参字段，默认是根据消费函数def定义的入参来生成这个。
    
    # 自定义覆盖类
    consumer_override_cls: typing.Optional[typing.Any]   # 自定义消费者类
    publisher_override_cls: typing.Optional[typing.Any]   # 自定义发布者类
    
    # 函数类型
    consuming_function_kind: typing.Optional[str]  # 函数类型：CLASS_METHOD/INSTANCE_METHOD/STATIC_METHOD/COMMON_FUNCTION
    
    # 用户自定义配置
    user_options: typing.Dict[str, typing.Any]  # 用户额外自定义的配置
    
    # 自动生成信息
    auto_generate_info: typing.Dict[str, typing.Any]  # 自动生成的信息,里面有个 final_func_input_params_info 存储了函数入参信息，用户也可以把这当做微服务的接口文档协议，让用户清楚知道消息需要传递哪些入参。

    

# 活跃消费者详细模型
class ActiveConsumerRunInfo(BaseAllowExtraModel):
    """
    单个活跃消费者的详细信息
    这些数据是从redis中的心跳信息获取的
    """
    # 基本信息
    queue_name: str  # 队列名
    computer_name: str  # 计算机名
    computer_ip: str  # 计算机IP地址
    process_id: int  # 进程ID
    consumer_id: int  # 消费者ID
    consumer_uuid: str  # 消费者UUID
    
    # 启动和心跳时间
    start_datetime_str: str  # 启动时间字符串，格式：YYYY-MM-DD HH:MM:SS
    start_timestamp: float  # 启动时间戳
    hearbeat_datetime_str: str  # 最近心跳时间字符串
    hearbeat_timestamp: float  # 最近心跳时间戳
    
    # 消费函数信息
    consuming_function: str  # 消费函数名
    code_filename: str  # 代码文件路径
    
    # 时间单位配置
    unit_time_for_count: int  # 统计的时间单位（秒）
    
    # 最近X秒执行统计
    last_x_s_execute_count: int  # 最近X秒执行次数
    last_x_s_execute_count_fail: int  # 最近X秒失败次数
    last_execute_task_time: float  # 最后一次执行任务的时间戳
    last_x_s_avarage_function_spend_time: typing.Optional[float]   # 最近X秒平均耗时（秒）
    last_x_s_total_cost_time: typing.Optional[float]  # 最近X秒总耗时（秒）
    
    # 消息队列状态
    msg_num_in_broker: int  # broker中的消息数量
    current_time_for_execute_task_times_every_unit_time: float  # 当前统计周期的开始时间戳
    last_timestamp_when_has_task_in_queue: float  # 最后一次队列有任务的时间戳
    
    # 从启动开始的统计
    total_consume_count_from_start: int  # 从启动开始的总执行次数
    total_consume_count_from_start_fail: int  # 从启动开始的总失败次数
    total_cost_time_from_start: float  # 从启动开始的总耗时（秒）
    avarage_function_spend_time_from_start: typing.Optional[float]  # 从启动开始的平均耗时（秒）


# 队列运行信息数据模型
class QueueParamsAndActiveConsumersData(BaseModel):
    """队列参数和活跃消费者数据"""
    queue_params: QueueParams  # 队列的booster入参大全
    active_consumers: typing.List[ActiveConsumerRunInfo]   # 队列对应的所有活跃消费者列表
    pause_flag: int  # 暂停标志
    msg_num_in_broker: int   # broker中的消息数量
    history_run_count: typing.Optional[int]   # 历史运行次数
    history_run_fail_count: typing.Optional[int]   # 历史失败次数
    all_consumers_last_x_s_execute_count: int   # 所有消费进程最近X秒所有消费者执行次数
    all_consumers_last_x_s_execute_count_fail: int   # 所有消费进程最近X秒所有消费者失败次数
    all_consumers_last_x_s_avarage_function_spend_time: typing.Optional[float]   # 所有消费进程最近X秒平均耗时
    all_consumers_avarage_function_spend_time_from_start: typing.Optional[float]   # 所有消费进程从启动开始的平均耗时
    all_consumers_total_consume_count_from_start: int   # 所有消费进程从启动开始总消费次数
    all_consumers_total_consume_count_from_start_fail: int   # 所有消费进程从启动开始总失败次数
    all_consumers_last_execute_task_time: typing.Optional[float]   # 所有消费进程中最后一次执行任务的时间戳


class QueueConfigData(BaseModel):
    """队列配置数据"""
    queues_config: typing.Dict[str, QueueParams] = {}
    count: int = 0


@fastapi_router.get("/get_queues_config", response_model=BaseResponse[QueueConfigData])
def get_queues_config():
    """
    获取所有队列的配置信息
    
    返回所有已注册队列的详细配置参数，包括：
    - 队列名称
    - broker 类型
    - 并发数量
    - QPS 限制
    - 是否启用 RPC 模式
    - ！！！重要，消费函数的入参名字列表在 auto_generate_info.final_func_input_params_info 中 ，用于发布消息时校验入参是否正确，不正确的消息格式立刻从接口返回报错消息内容不正确。
      前端或跨部门可以先获取所有队列名字以及队列对应的配置，就知道rpc publish发布接口可以传哪些queue_name以及对应的消息应该包含哪些字段。
      auto_generate_info.final_func_input_params_info ，相当于是funboost能自动根据消费函数的def定义，对外提供消费函数的接口文档字段，就类似fastapi自动对接口函数入参生成了文档，避免需要重复手动一个个的编辑接口文档字段。
    - 等等其他 @boost 装饰器的所有参数
    
    主要用于前端可视化展示和管理
    """
    try:
        queues_config = QueuesConusmerParamsGetter().get_queues_params()
        
        return BaseResponse[QueueConfigData](
            succ=True,
            msg="获取成功",
            data=QueueConfigData(
                queues_config=queues_config,
                count=len(queues_config)
            )
        )
    except Exception as e:
        logger.exception(f'获取队列配置失败: {str(e)}')
        return BaseResponse[QueueConfigData](
            succ=False,
            msg=f"获取队列配置失败: {str(e)}",
            data=QueueConfigData(
                queues_config={},
                count=0
            )
        )


@fastapi_router.get("/get_one_queue_config", response_model=BaseResponse[QueueParams])
@handle_funboost_exceptions
def get_one_queue_config(queue_name: str):
    """
    获取单个队列的配置信息
    
    参数:
        queue_name: 队列名称（必填）
    
    返回:
        队列的配置信息，包括函数入参信息 (auto_generate_info.final_func_input_params_info)
    """
    queue_params = SingleQueueConusmerParamsGetter(queue_name).get_one_queue_params()
    
    return BaseResponse[QueueParams](
        succ=True,
        msg="获取成功",
        data=queue_params
    )
@fastapi_router.get("/get_queue_run_info", response_model=BaseResponse[QueueParamsAndActiveConsumersData])
def get_queue_run_info(queue_name: str):
    """
    获取单个队列的运行信息
    
    参数:
        queue_name: 队列名称（必填）
    
    返回:
        队列的详细运行信息，包括：
        - queue_params: 队列配置参数
        - active_consumers: 活跃的消费者列表
        - pause_flag: 暂停标志（-1,0表示未暂停，1表示已暂停）
        - msg_num_in_broker: broker中的消息数量（实时）
        - history_run_count: 历史运行总次数
        - history_run_fail_count: 历史失败总次数
        - all_consumers_last_x_s_execute_count: 所有消费进程，最近X秒所有消费者的执行次数
        - all_consumers_last_x_s_execute_count_fail: 所有消费进程，最近X秒所有消费者的失败次数
        - all_consumers_last_x_s_avarage_function_spend_time: 所有消费进程，最近X秒的平均函数耗时
        - all_consumers_avarage_function_spend_time_from_start: 所有消费进程，从启动开始的平均函数耗时
        - all_consumers_total_consume_count_from_start: 所有消费进程，从启动开始的总消费次数
        - all_consumers_total_consume_count_from_start_fail: 所有消费进程，从启动开始的总失败次数
        - all_consumers_last_execute_task_time: 所有消费进程中，最后一次执行任务的时间戳
    """
    try:
        # 获取单个队列的运行信息
        queue_info = SingleQueueConusmerParamsGetter(queue_name).get_one_queue_params_and_active_consumers()
        
        return BaseResponse[QueueParamsAndActiveConsumersData](
            succ=True,
            msg="获取成功",
            data=QueueParamsAndActiveConsumersData(**queue_info)
        )
        
    except Exception as e:
        logger.exception(f'获取队列运行信息失败: {str(e)}')
        return BaseResponse[QueueParamsAndActiveConsumersData](
            succ=False,
            msg=f"获取队列运行信息失败: {str(e)}",
            data=None
        )


# 所有队列运行信息数据模型
class AllQueuesRunInfoData(BaseModel):
    """所有队列的运行信息"""
    queues: typing.Dict[str, QueueParamsAndActiveConsumersData]  # 队列名到队列运行信息的映射
    total_count: int  # 队列总数


@fastapi_router.get("/get_all_queue_run_info", response_model=BaseResponse[AllQueuesRunInfoData])
def get_all_queue_run_info():
    """
    获取所有队列的运行信息
    
    返回:
        所有队列的详细运行信息，包括每个队列的：
        - queue_params: 队列配置参数
        - active_consumers: 活跃的消费者列表
        - pause_flag: 暂停标志
        - msg_num_in_broker: broker中的消息数量
        - history_run_count: 历史运行总次数
        - history_run_fail_count: 历史失败总次数
        - 以及各种统计信息
    """
    try:
        # 获取所有队列的运行信息
        all_queues_info = QueuesConusmerParamsGetter().get_queues_params_and_active_consumers()
        print(all_queues_info)
        
        # 转换为 Pydantic 模型
        queues_data = {}
        for queue_name, queue_info in all_queues_info.items():
            queues_data[queue_name] = QueueParamsAndActiveConsumersData(**queue_info)
        
        return BaseResponse[AllQueuesRunInfoData](
            succ=True,
            msg="获取成功",
            data=AllQueuesRunInfoData(
                queues=queues_data,
                total_count=len(queues_data)
            )
        )
        
    except Exception as e:
        logger.exception(f'获取所有队列运行信息失败: {str(e)}')
        return BaseResponse[AllQueuesRunInfoData](
            succ=False,
            msg=f"获取所有队列运行信息失败: {str(e)}",
            data=None
        )

# ==================== 定时任务管理接口 ====================


# 定时任务相关数据模型
class TimingJobRequest(BaseModel):
    """添加定时任务请求"""
    queue_name: str  # 队列名称
    trigger: str  # 触发器类型: 'date', 'interval', 'cron'
    job_id: typing.Optional[str] = None  # 任务ID，如果不提供则自动生成
    job_store_kind: str = 'redis'  # 任务存储方式: 'redis' 或 'memory'
    replace_existing: bool = False  # 是否替换已存在的任务
    
    # 任务参数
    args: typing.Optional[typing.List] = None  # 位置参数
    kwargs: typing.Optional[typing.Dict] = None  # 关键字参数
    
    # date 触发器参数
    run_date: typing.Optional[str] = None  # 运行时间，格式: 'YYYY-MM-DD HH:MM:SS'
    
    # interval 触发器参数
    weeks: typing.Optional[int] = None
    days: typing.Optional[int] = None
    hours: typing.Optional[int] = None
    minutes: typing.Optional[int] = None
    seconds: typing.Optional[int] = None
    
    # cron 触发器参数
    year: typing.Optional[str] = None
    month: typing.Optional[str] = None
    day: typing.Optional[str] = None
    week: typing.Optional[str] = None
    day_of_week: typing.Optional[str] = None
    hour: typing.Optional[str] = None
    minute: typing.Optional[str] = None
    second: typing.Optional[str] = None


class TimingJobData(BaseModel):
    """定时任务数据"""
    job_id: str
    queue_name: typing.Optional[str] = None
    trigger: typing.Optional[str] = None
    next_run_time: typing.Optional[str] = None
    status: typing.Optional[str] = None  # "running" 或 "paused"
    kwargs: typing.Optional[typing.Dict] = None  # 任务的 kwargs 参数


class TimingJobListData(BaseModel):
    """定时任务列表数据"""
    jobs_by_queue: typing.Dict[str, typing.List[TimingJobData]] = {}  # 按队列分组的任务
    total_count: int = 0





@fastapi_router.post("/add_timing_job", response_model=BaseResponse[TimingJobData])
def add_timing_job(job_request: TimingJobRequest):
    """
    添加定时任务
    
    支持三种触发方式:
    1. date: 在指定日期时间执行一次
       - 需要提供: run_date
       - 示例: {"trigger": "date", "run_date": "2025-12-03 15:00:00"}
    
    2. interval: 按固定时间间隔执行
       - 需要提供: weeks, days, hours, minutes, seconds 中的至少一个
       - 示例: {"trigger": "interval", "seconds": 10}
    
    3. cron: 按cron表达式执行
       - 需要提供: year, month, day, week, day_of_week, hour, minute, second 中的至少一个
       - 示例: {"trigger": "cron", "hour": "*/2", "minute": "30"}
    """
    try:
        # 获取 job_adder
        job_adder = gen_aps_job_adder(job_request.queue_name, job_request.job_store_kind)

        # 构建触发器参数
        trigger_args = {}
        
        if job_request.trigger == 'date':
            if job_request.run_date:
                trigger_args['run_date'] = job_request.run_date
        
        elif job_request.trigger == 'interval':
            if job_request.weeks is not None:
                trigger_args['weeks'] = job_request.weeks
            if job_request.days is not None:
                trigger_args['days'] = job_request.days
            if job_request.hours is not None:
                trigger_args['hours'] = job_request.hours
            if job_request.minutes is not None:
                trigger_args['minutes'] = job_request.minutes
            if job_request.seconds is not None:
                trigger_args['seconds'] = job_request.seconds
        
        elif job_request.trigger == 'cron':
            if job_request.year is not None:
                trigger_args['year'] = job_request.year
            if job_request.month is not None:
                trigger_args['month'] = job_request.month
            if job_request.day is not None:
                trigger_args['day'] = job_request.day
            if job_request.week is not None:
                trigger_args['week'] = job_request.week
            if job_request.day_of_week is not None:
                trigger_args['day_of_week'] = job_request.day_of_week
            if job_request.hour is not None:
                trigger_args['hour'] = job_request.hour
            if job_request.minute is not None:
                trigger_args['minute'] = job_request.minute
            if job_request.second is not None:
                trigger_args['second'] = job_request.second
        
        # 添加任务
        job = job_adder.add_push_job(
            trigger=job_request.trigger,
            args=job_request.args,
            kwargs=job_request.kwargs,
            id=job_request.job_id,
            replace_existing=job_request.replace_existing,
            **trigger_args
        )

        return BaseResponse[TimingJobData](
            succ=True,
            msg="定时任务添加成功",
            data=TimingJobData(
                job_id=job.id,
                queue_name=job_request.queue_name,
                trigger=str(job.trigger),
                next_run_time=str(job.next_run_time) if job.next_run_time else None,
                status="running",
                kwargs=job_request.kwargs
            )
        )
        
    except Exception as e:
        logger.exception(f'添加定时任务失败: {str(e)}')
        return BaseResponse[TimingJobData](
            succ=False,
            msg=f"添加定时任务失败: {str(e)}\n{traceback.format_exc()}",
            data=None
        )


@fastapi_router.get("/get_timing_jobs", response_model=BaseResponse[TimingJobListData])
def get_timing_jobs(
    queue_name: typing.Optional[str] = None,
    job_store_kind: str = 'redis'
):
    """
    获取定时任务列表
    
    参数:
        queue_name: 队列名称（可选，如果不提供则获取所有队列的任务）
        job_store_kind: 任务存储方式，'redis' 或 'memory'
    
    返回格式:
        jobs_by_queue: {queue_name: [jobs]}，按队列分组的任务
        total_count: 总任务数
    """
    try:
        # 使用字典格式存储：{queue_name: [jobs]}
        jobs_by_queue: typing.Dict[str, typing.List[TimingJobData]] = {}
        total_count = 0
        
        if queue_name:
            # 获取指定队列的任务
            jobs_by_queue[queue_name] = []
            try:
                job_adder = gen_aps_job_adder(queue_name, job_store_kind)
                jobs = job_adder.aps_obj.get_jobs()
                
                for job in jobs:
                    status = "paused" if job.next_run_time is None else "running"
                    kwargs = job.kwargs if hasattr(job, 'kwargs') and job.kwargs else {}
                    jobs_by_queue[queue_name].append(TimingJobData(
                        job_id=job.id,
                        queue_name=queue_name,
                        trigger=str(job.trigger),
                        next_run_time=str(job.next_run_time) if job.next_run_time else None,
                        status=status,
                        kwargs=kwargs
                    ))
                    total_count += 1
            except Exception as e:
                logger.exception(f'获取定时任务列表失败: {str(e)}')
                pass  # 队列不存在或没有任务，保持空数组
        else:
            # 获取所有队列的任务
            all_queues = list(QueuesConusmerParamsGetter().get_all_queue_names())
            for q_name in all_queues:
                jobs_by_queue[q_name] = []  # 初始化为空数组
                try:
                    job_adder = gen_aps_job_adder(q_name, job_store_kind)
                    jobs = job_adder.aps_obj.get_jobs()
                    
                    for job in jobs:
                        status = "paused" if job.next_run_time is None else "running"
                        kwargs = job.kwargs if hasattr(job, 'kwargs') and job.kwargs else {}
                        jobs_by_queue[q_name].append(TimingJobData(
                            job_id=job.id,
                            queue_name=q_name,
                            trigger=str(job.trigger),
                            next_run_time=str(job.next_run_time) if job.next_run_time else None,
                            status=status,
                            kwargs=kwargs
                        ))
                        total_count += 1
                except Exception as e:
                    logger.exception(f'获取定时任务列表失败: {str(e)}')
                    pass  # 队列没有任务或出错，保持空数组
        
        return BaseResponse[TimingJobListData](
            succ=True,
            msg="获取成功",
            data=TimingJobListData(
                jobs_by_queue=jobs_by_queue,
                total_count=total_count
            )
        )
        
    except Exception as e:
        logger.exception(f'获取定时任务列表失败: {str(e)}')
        return BaseResponse[TimingJobListData](
            succ=False,
            msg=f"获取定时任务列表失败: {str(e)}",
            data=TimingJobListData(jobs_by_queue={}, total_count=0)
        )


@fastapi_router.get("/get_timing_job", response_model=BaseResponse[TimingJobData])
def get_timing_job(
    job_id: str,
    queue_name: str,
    job_store_kind: str = 'redis'
):
    """
    获取单个定时任务的详细信息
    
    参数:
        job_id: 任务ID（必填）
        queue_name: 队列名称（必填）
        job_store_kind: 任务存储方式，'redis' 或 'memory'
    
    返回:
        任务的详细信息，包括任务ID、队列名、触发器类型、下次运行时间等
    """
    try:
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        
        # 获取指定的任务
        job = job_adder.aps_obj.get_job(job_id)
        
        if job:
            status = "paused" if job.next_run_time is None else "running"
            kwargs = job.kwargs if hasattr(job, 'kwargs') and job.kwargs else {}
            return BaseResponse[TimingJobData](
                succ=True,
                msg="获取成功",
                data=TimingJobData(
                    job_id=job.id,
                    queue_name=queue_name,
                    trigger=str(job.trigger),
                    next_run_time=str(job.next_run_time) if job.next_run_time else None,
                    status=status,
                    kwargs=kwargs
                )
            )
        else:
            return BaseResponse[TimingJobData](
                succ=False,
                msg=f"任务 {job_id} 不存在",
                data=None
            )
        
    except Exception as e:
        logger.exception(f'获取定时任务失败: {str(e)}')
        return BaseResponse[TimingJobData](
            succ=False,
            msg=f"获取定时任务失败: {str(e)}",
            data=None
        )


@fastapi_router.delete("/delete_timing_job", response_model=BaseResponse)
def delete_timing_job(
    job_id: str,
    queue_name: str,
    job_store_kind: str = 'redis'
):
    """
    删除定时任务
    
    参数:
        job_id: 任务ID
        queue_name: 队列名称
        job_store_kind: 任务存储方式，'redis' 或 'memory'
    """
    try:
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        job_adder.aps_obj.remove_job(job_id)
        
        return BaseResponse(
            succ=True,
            msg=f"定时任务 {job_id} 删除成功",
            data=None
        )
        
    except Exception as e:
        logger.exception(f'删除定时任务失败: {str(e)}')
        return BaseResponse(
            succ=False,
            msg=f"删除定时任务失败: {str(e)}",
            data=None
        )


class DeleteAllJobsData(BaseModel):
    """删除所有任务的结果数据"""
    deleted_count: int = 0
    failed_jobs: typing.List[str] = []


@fastapi_router.delete("/delete_all_timing_jobs", response_model=BaseResponse[DeleteAllJobsData])
def delete_all_timing_jobs(
    queue_name: typing.Optional[str] = None,
    job_store_kind: str = 'redis'
):
    """
    删除所有定时任务
    
    参数:
        queue_name: 队列名称（可选，如果不提供则删除所有队列的所有任务）
        job_store_kind: 任务存储方式，'redis' 或 'memory'
    
    返回:
        deleted_count: 成功删除的任务数量
        failed_jobs: 删除失败的任务ID列表
    """
    try:
        deleted_count = 0
        failed_jobs = []
        
        if queue_name:
            # 删除指定队列的所有任务
            try:

                job_adder = gen_aps_job_adder(queue_name, job_store_kind)
                jobs = job_adder.aps_obj.get_jobs()
                
                for job in jobs:
                    try:
                        job_adder.aps_obj.remove_job(job.id)
                        deleted_count += 1
                    except Exception as e:
                        failed_jobs.append(f"{job.id}: {str(e)}")
            except Exception as e:
                return BaseResponse[DeleteAllJobsData](
                    succ=False,
                    msg=f"删除队列 {queue_name} 的任务失败: {str(e)}",
                    data=DeleteAllJobsData(
                        deleted_count=deleted_count,
                        failed_jobs=failed_jobs
                    )
                )
        else:
            # 删除所有队列的所有任务
            all_queues = list(QueuesConusmerParamsGetter().get_all_queue_names())
            for q_name in all_queues:
                try:

                    job_adder = gen_aps_job_adder(q_name, job_store_kind)
                    jobs = job_adder.aps_obj.get_jobs()
                    
                    for job in jobs:
                        try:
                            job_adder.aps_obj.remove_job(job.id)
                            deleted_count += 1
                        except Exception as e:
                            failed_jobs.append(f"{q_name}/{job.id}: {str(e)}")
                except Exception as e:
                    logger.exception(f'删除队列 {q_name} 的任务失败: {str(e)}')
                    # 队列没有任务或出错，继续处理下一个队列
                    pass
        
        return BaseResponse[DeleteAllJobsData](
            succ=True,
            msg=f"成功删除 {deleted_count} 个定时任务",
            data=DeleteAllJobsData(
                deleted_count=deleted_count,
                failed_jobs=failed_jobs
            )
        )
        
    except Exception as e:
        logger.exception(f'删除所有定时任务失败: {str(e)}')
        return BaseResponse[DeleteAllJobsData](
            succ=False,
            msg=f"删除所有定时任务失败: {str(e)}",
            data=DeleteAllJobsData(
                deleted_count=0,
                failed_jobs=[]
            )
        )


@fastapi_router.post("/pause_timing_job", response_model=BaseResponse)
def pause_timing_job(
    job_id: str,
    queue_name: str,
    job_store_kind: str = 'redis'
):
    """
    暂停定时任务
    
    参数:
        job_id: 任务ID
        queue_name: 队列名称
        job_store_kind: 任务存储方式，'redis' 或 'memory'
    """
    try:
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        job_adder.aps_obj.pause_job(job_id)
        
        return BaseResponse(
            succ=True,
            msg=f"定时任务 {job_id} 已暂停",
            data=None
        )
        
    except Exception as e:
        logger.exception(f'暂停定时任务失败: {str(e)}')
        return BaseResponse(
            succ=False,
            msg=f"暂停定时任务失败: {str(e)}",
            data=None
        )


@fastapi_router.post("/resume_timing_job", response_model=BaseResponse)
def resume_timing_job(
    job_id: str,
    queue_name: str,
    job_store_kind: str = 'redis'
):
    """
    恢复定时任务
    
    参数:
        job_id: 任务ID
        queue_name: 队列名称
        job_store_kind: 任务存储方式，'redis' 或 'memory'
    """
    try:
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        job_adder.aps_obj.resume_job(job_id)
        
        return BaseResponse(
            succ=True,
            msg=f"定时任务 {job_id} 已恢复",
            data=None
        )
        
    except Exception as e:
        logger.exception(f'恢复定时任务失败: {str(e)}')
        return BaseResponse(
            succ=False,
            msg=f"恢复定时任务失败: {str(e)}",
            data=None
        )


@fastapi_router.delete("/deprecate_queue", response_model=BaseResponse[DeprecateQueueData])
@handle_funboost_exceptions
async def deprecate_queue(request: DeprecateQueueRequest):
    """
    废弃队列 - 从 Redis 的 funboost_all_queue_names set 中移除队列名
    
    Args:
        request: 包含要废弃的队列名称
        
    Returns:
        BaseResponse[DeprecateQueueData]: 包含废弃结果
        
    使用场景:
        当队列改名或不再使用时，可以调用此接口将其从队列列表中移除
    """
    queue_name = request.queue_name
    
    # 调用 SingleQueueConusmerParamsGetter 的 deprecate_queue 方法
    SingleQueueConusmerParamsGetter(queue_name).deprecate_queue()
    
    logger.info(f'成功废弃队列: {queue_name}')
    return BaseResponse(
        succ=True,
        msg=f"成功废弃队列: {queue_name}",
        data=DeprecateQueueData(
            queue_name=queue_name,
            removed=True
        )
    )


# ==================== Scheduler Control Endpoints ====================

class SchedulerStatusData(BaseModel):
    queue_name: str
    status_code: int
    status_str: str

class SchedulerControlData(BaseModel):
    queue_name: str
    status_str: str

@fastapi_router.get("/get_scheduler_status", response_model=BaseResponse[SchedulerStatusData])
@handle_funboost_exceptions
def get_scheduler_status(
    queue_name: str = Query(..., description="队列名称"),
    job_store_kind: str = Query("redis", description="任务存储方式，'redis' 或 'memory'，默认 'redis'")
):
    """
    获取定时器调度器状态
    """
    
    job_adder = gen_aps_job_adder(queue_name, job_store_kind)
    
    state_map = {0: 'stopped', 1: 'running', 2: 'paused'}
    state = job_adder.aps_obj.state
    
    return BaseResponse(
        succ=True,
        msg="获取成功",
        data=SchedulerStatusData(
            queue_name=queue_name,
            status_code=state,
            status_str=state_map.get(state, 'unknown')
        )
    )


@fastapi_router.post("/pause_scheduler", response_model=BaseResponse[SchedulerControlData])
@handle_funboost_exceptions
def pause_scheduler(
    queue_name: str = Query(..., description="队列名称"),
    job_store_kind: str = Query("redis", description="任务存储方式，'redis' 或 'memory'，默认 'redis'")
):
    """
    暂停定时器调度器
    注意：这只会暂停当前进程中的调度器实例。如果部署了多实例，可能需要单独控制。
    """
    job_adder = gen_aps_job_adder(queue_name, job_store_kind)
    job_adder.aps_obj.pause()
    
    return BaseResponse(
        succ=True,
        msg=f"调度器已暂停 ({queue_name})",
        data=SchedulerControlData(
            queue_name=queue_name,
            status_str="paused"
        )
    )


@fastapi_router.post("/resume_scheduler", response_model=BaseResponse[SchedulerControlData])
@handle_funboost_exceptions
def resume_scheduler(
    queue_name: str = Query(..., description="队列名称"),
    job_store_kind: str = Query("redis", description="任务存储方式，'redis' 或 'memory'，默认 'redis'")
):
    """
    恢复运行定时器调度器
    """
    job_adder = gen_aps_job_adder(queue_name, job_store_kind)
    job_adder.aps_obj.resume()
    
    return BaseResponse(
        succ=True,
        msg=f"调度器已恢复运行 ({queue_name})",
        data=SchedulerControlData(
            queue_name=queue_name,
            status_str="running"
        )
    )


# ==================== care_project_name 项目筛选接口 ====================

class CareProjectNameData(BaseModel):
    """care_project_name 响应数据"""
    care_project_name: typing.Optional[str] = None


class SetCareProjectNameRequest(BaseModel):
    """设置 care_project_name 请求模型"""
    care_project_name: str = ""  # 空字符串表示不限制


class AllProjectNamesData(BaseModel):
    """所有项目名称响应数据"""
    project_names: typing.List[str] = []
    count: int = 0


@fastapi_router.get("/get_care_project_name", response_model=BaseResponse[CareProjectNameData])
@handle_funboost_exceptions
def get_care_project_name(response: Response):
    """
    获取当前的 care_project_name 设置
    
    返回:
        care_project_name: 当前设置的项目名称，None 表示不限制（显示全部）
    """
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    care_project_name = CareProjectNameEnv.get()
    
    return BaseResponse(
        succ=True,
        msg="获取成功",
        data=CareProjectNameData(
            care_project_name=care_project_name
        )
    )


@fastapi_router.post("/set_care_project_name", response_model=BaseResponse[CareProjectNameData])
@handle_funboost_exceptions
def set_care_project_name(request: SetCareProjectNameRequest):
    """
    设置 care_project_name
    
    请求体:
        care_project_name: 项目名称，空字符串表示不限制（显示全部项目）
    
    说明:
        设置后会影响本次会话的所有页面（队列操作、消费者信息等）
    """
    care_project_name = request.care_project_name
    
    # 空字符串表示清除限制
    CareProjectNameEnv.set(care_project_name)
    
    # 如果设置为空字符串，返回时显示为 None
    display_value = care_project_name if care_project_name else None
    
    logger.info(f'设置 care_project_name 为: {display_value}')
    return BaseResponse(
        succ=True,
        msg=f"设置成功: {display_value if display_value else '不限制（显示全部）'}",
        data=CareProjectNameData(
            care_project_name=display_value
        )
    )


@fastapi_router.get("/get_all_project_names", response_model=BaseResponse[AllProjectNamesData])
@handle_funboost_exceptions
def get_all_project_names(response: Response):
    """
    获取所有已注册的项目名称列表
    
    返回:
        project_names: 项目名称列表（按字母排序）
        count: 项目数量
    """
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    # 使用 QueuesConusmerParamsGetter 获取所有项目名称
    project_names = QueuesConusmerParamsGetter().get_all_project_names()
    
    return BaseResponse(
        succ=True,
        msg="获取成功",
        data=AllProjectNamesData(
            project_names=sorted(project_names) if project_names else [],
            count=len(project_names) if project_names else 0
        )
    )


# 运行应用 (仅在作为主脚本运行时创建 app)
if __name__ == "__main__":
    import uvicorn

    CareProjectNameEnv.set('test_project1')

    # 这是一个示例，展示用户如何将 funboost router 集成到自己的 app 中
    app = FastAPI()
    app.include_router(fastapi_router)
    # 注意：funboost router 的异常处理使用装饰器 @handle_funboost_exceptions，无需全局注册


    print("启动 Funboost API 服务...")
    print("接口文档: http://127.0.0.1:16666/docs")
    uvicorn.run(app, host="0.0.0.0", port=16666, )
