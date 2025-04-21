

import asyncio

async def main():
    print("Hello, world!")
    await asyncio.sleep(1)
    print("Goodbye, world!")
    print("Current event loop:", id(loop))

# 创建一个新的事件循环
loop = asyncio.new_event_loop()
print("loop:", id(loop))
# 不设置默认事件循环，直接使用 loop 运行异步函数
print("Running without setting default event loop:")
loop.run_until_complete(main())

# # 尝试获取当前事件循环，这里可能会出现问题
# try:
#     current_loop = asyncio.get_event_loop()
#     print("Current event loop without setting:", current_loop)
# except RuntimeError as e:
#     print("Error when getting event loop without setting:", e)
#
# # 正确的方式是设置默认事件循环
# asyncio.set_event_loop(loop)
# print("\nRunning with setting default event loop:")
# loop.run_until_complete(main())
#
# # 现在获取当前事件循环是正确的
# current_loop = asyncio.get_event_loop()
# print("Current event loop after setting:", current_loop)
#
# # 最后，关闭事件循环
# loop.close()