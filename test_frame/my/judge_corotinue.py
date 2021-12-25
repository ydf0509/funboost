import asyncio
async  def f(x):
    return x*2


from decorator_libs import TimerContextManager

with TimerContextManager():
    for i in range(10000):
        # print(asyncio.iscoroutine(f(5)))
        # print(asyncio.iscoroutine(7))
        print(7)