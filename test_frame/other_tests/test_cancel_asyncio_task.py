import asyncio


async def my_coroutine():
    try:
        print("协程开始")
        await asyncio.sleep(10)  # 模拟长时间运行的任务
        print("协程完成")
    except asyncio.CancelledError:
        print("协程被取消")
    finally:
        print("清理资源")


async def main():
    # 创建协程任务
    task = asyncio.create_task(my_coroutine())

    await asyncio.sleep(1)  # 等待一下，确保协程开始
    print("准备取消协程")

    # 取消协程
    task.cancel()

    try:
        await task  # 等待任务被取消
    except asyncio.CancelledError:
        print("任务已被取消")


# 运行主程序

asyncio.run(main())

