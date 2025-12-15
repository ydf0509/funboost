"""
演示 Funboost Router 异常处理装饰器的测试代码
注意：使用装饰器方式，不影响用户自己的 FastAPI app
"""

from fastapi import FastAPI
from funboost.faas.fastapi_adapter import fastapi_router, handle_funboost_exceptions, BaseResponse
from funboost.core.exceptions import QueueNameNotExists, FuncParamsError

# 创建 FastAPI 应用
app = FastAPI(title="Funboost Router 异常处理装饰器测试")

# 1. 引入 funboost router（装饰器已经应用在 router 的接口上）
app.include_router(fastapi_router)

# 注意：不需要注册全局异常处理器！
# funboost router 的异常处理通过 @handle_funboost_exceptions 装饰器实现
# 这样不会影响用户自己的 app


# ==================== 测试接口 ====================
# 这些是用户自己的接口，可以选择性地使用装饰器

@app.get("/test/funboost_exception")
@handle_funboost_exceptions  # 使用装饰器
def test_funboost_exception():
    """
    测试 FunboostException 异常处理
    访问这个接口会抛出 QueueNameNotExists 异常
   装饰器会自动捕获并返回统一格式的错误
    """
    # 模拟抛出 FunboostException
    raise QueueNameNotExists(
        message="测试队列不存在",
        data={"queue_name": "test_queue", "available_queues": ["queue1", "queue2"]}
    )


@app.get("/test/normal_exception")
@handle_funboost_exceptions  # 使用装饰器
def test_normal_exception():
    """
    测试普通异常处理
    访问这个接口会抛出 ValueError
    装饰器会自动捕获并返回包含堆栈信息的错误
    """
    # 模拟抛出普通异常
    x = "not a number"
    return int(x)  # 这会抛出 ValueError


@app.get("/test/func_params_error")
@handle_funboost_exceptions  # 使用装饰器
def test_func_params_error():
    """
    测试函数参数错误异常
    """
    error_data = {
        'your_now_publish_params_keys_list': ['a', 'b'],
        'right_func_input_params_list_info': {
            'must_arg_name_list': ['a', 'b', 'c'],
            'optional_arg_name_list': []
        },
    }
    raise FuncParamsError('Invalid parameters for consuming function', data=error_data)


@app.get("/test/success")
@handle_funboost_exceptions  # 使用装饰器
def test_success():
    """
    测试正常返回
    这个接口不会抛出异常
    注意：成功响应中 error、traceback、trace_id 都为 None
    """
    return BaseResponse(
        succ=True,
        msg="测试成功",
        code=200,
        data={"message": "这是一个成功的响应"},
        error=None,  # 成功时error为None
        traceback=None,  # 成功时traceback为None
        trace_id=None  # 也可以在成功时设置trace_id用于追踪
    )


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("Funboost 全局异常处理器测试服务已启动")
    print("=" * 60)
    print()
    print("访问以下地址进行测试:")
    print()
    print("1. API文档: http://127.0.0.1:8888/docs")
    print()
    print("2. 测试接口:")
    print("   - http://127.0.0.1:8888/test/funboost_exception  (FunboostException)")
    print("   - http://127.0.0.1:8888/test/normal_exception    (普通异常)")
    print("   - http://127.0.0.1:8888/test/func_params_error   (函数参数错误)")
    print("   - http://127.0.0.1:8888/test/success             (成功响应)")
    print()
    print("3. Funboost接口:")
    print("   - http://127.0.0.1:8888/funboost/get_all_queues")
    print()
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8888)
