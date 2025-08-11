"""
此文件演示, funboost 使用 rpc获取结果阻塞的特性,来实现 canvas编排
可以把一个函数的结果作为下一个函数的入参,来实现 canvas编排
无需学习新的领域特定语言（DSL） 没有发明新的语法.funboost没有为工作流编排引入任何新的、专门的 API

整个编排过程就是调用 funboost 已有的 .push() / .aio_push() 和 .wait_rpc_data_or_raise() 方法。
开发者不需要去学习和记忆 chain, chord, group,header,body, s (signature), si,s(immutable=True), map,starmap  
等特定的 Canvas 概念和语法，降低了学习成本。
这一切都是用户主动使用funboost的rpc特性来实现,用户可以自由灵活控制
"""


"""
此文件演示一个非常经典的canvas编排:
    1.从url下载视频,并保存到本地 (download_video)
    2.根据第1步下载的视频文件,转码视频,并发转换成3个分辨率的视频文件 (transform_video)
    3.根据第2步转码的视频文件列表,更新数据库,并且发送微信通知 (send_finish_msg)


        
这个需求如果在celery的canvas编排是如下:
    from celery import chain, chord, group

    resolutions = ["360p", "720p", "1080p"]

    # header: 并行转码；body: 汇总并发送完成消息
    header = group(transform_video.s(resolution=r) for r in resolutions)
    body = send_finish_msg.s(url=url)

    # 先下载 -> 将下载结果（文件路径）作为额外参数传给 header 中每个 transform_video
    work_flow = chain(
        download_video.s(url),
        chord(header, body)
    )
"""

"""
celery发明了一套声明式canvas api,用户需要学习新的语法,
funboost是命令式,全部使用已有的rpc方法,没有一套声明式api
"""


import typing

import os
import sys
import time

os.environ['path'] = os.path.dirname(sys.executable) + os.pathsep + os.environ['PATH']

from funboost import (boost, BoosterParams, BrokerEnum, ctrl_c_recv,
                      ConcurrentModeEnum, AsyncResult,FunctionResultStatus,
                      BoostersManager, AioAsyncResult, fct
                      )


class MyBoosterParams(BoosterParams):
    is_using_rpc_mode: bool = True
    broker_exclusive_config: dict = {'pull_msg_batch_size': 1}
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
    max_retry_times: int = 0


@boost(MyBoosterParams(queue_name='download_video_queue'))
def download_video(url):
    """下载视频"""
    # 1/0  # 这个是模拟 任务编排,其中某个环节报错
    mock_need_time = 5
    time.sleep(mock_need_time)
    download_file = f'/dir/vd0/{url}'
    fct.logger.info(f'下载视频 {url} 完成, 保存到 {download_file},耗时{mock_need_time}秒')
    return download_file


@boost(MyBoosterParams(queue_name='transform_video_queue'))
def transform_video(video_file, resolution='360p'):
    """转码视频"""
    mock_need_time = 10
    time.sleep(mock_need_time)
    transform_file = f'{video_file}_{resolution}'
    fct.logger.info(f'转码视频 {video_file} 完成, 保存到 {transform_file},耗时{mock_need_time}秒')
    return transform_file


@boost(MyBoosterParams(queue_name='send_finish_msg_queue'))
def send_finish_msg(transform_video_file_list: list, url):
    """3个清晰度的视频都转码完成后,汇总结果发送微信通知"""
    mock_need_time = 2
    time.sleep(mock_need_time)
    fct.logger.info(f'更新数据库,并且发送微信通知 {url} 视频转码完成 {transform_video_file_list} ,耗时{mock_need_time}秒')
    return f'ok! {url} 下载 -> 转码3个清晰度格式视频 {transform_video_file_list} -> 更新数据库,发送微信通知 完成'


@boost(MyBoosterParams(queue_name='canvas_task_queue',concurrent_num=500))
def canvas_task(url):


    """
    funboost显式的把上一个函数交给或者结果列表传递给下一个函数,思路很清晰.用户可以在里面写各种if else判断,
    以及上一个节点错误是否还调用下一个节点.
    
    celery的canvas 自动把上一个函数的结果作为下一个函数的第一个入参,那里面的传递关系不清晰关系不明显不符合直觉,不透明.
    如果涉及到非常复杂的编排,用户很难使用celery 的语法写出正确的canvas编排,还不如使用rpc清晰易懂.
    """

   
    r1: AsyncResult = download_video.push(url).set_timeout(1000) # 用户可以设置rpc最大等待时间.
    rpc_res_file:FunctionResultStatus = r1.wait_rpc_data_or_raise(raise_exception=True)

    r2_list: typing.List[AsyncResult] = [transform_video.push(rpc_res_file.result, resolution=rel)
                                  for rel in ['360p', '720p', '1080p']]
    rpc_res_list = AsyncResult.batch_wait_rpc_data_or_raise(r2_list, raise_exception=True)
    transform_video_file_list = [one.result for one in rpc_res_list]

    r3 = send_finish_msg.push(transform_video_file_list, url)
    return r3.wait_rpc_data_or_raise(raise_exception=True).result


@boost(MyBoosterParams(queue_name='aio_canvas_task_queue',
                       concurrent_mode=ConcurrentModeEnum.ASYNC, # 使用asyncio异步阻塞的方式来实现canvas编排
                       concurrent_num=500))
async def aio_canvas_task(url):
    # 用户自己对比和canvas_task的相同点和差异.
    """演示 ,使用asyncio 来等待rpc结果, 减少系统线程占用数量"""
    r1: AioAsyncResult = await download_video.aio_push(url)
    rpc_res_file:FunctionResultStatus = await r1.wait_rpc_data_or_raise(raise_exception=True)

    r2_list: typing.List[AioAsyncResult] = [(await transform_video.aio_push(rpc_res_file.result, resolution=rel)).set_timeout(2000)
                                     for rel in ['360p', '720p', '1080p']]
    rpc_res_list = await AioAsyncResult.batch_wait_rpc_data_or_raise(r2_list, raise_exception=True)
    transform_video_file_list = [one.result for one in rpc_res_list]

    r3 = await send_finish_msg.aio_push(transform_video_file_list, url)
    return (await r3.wait_rpc_data_or_raise(raise_exception=True)).result


if __name__ == '__main__':
    download_video.consume()
    transform_video.consume()
    send_finish_msg.consume()
    canvas_task.consume()  # 演示使用同步阻塞的方式来实现canvas编排
    aio_canvas_task.consume()  # 演示使用asyncio异步阻塞的方式来实现canvas编排

    r4_a = canvas_task.push(f'funboost_url_video_a')
    print(r4_a.wait_rpc_data_or_raise(raise_exception=False).to_pretty_json_str())
    print('funboost_url_video_a 下载->转码->通知 耗时', r4_a.rpc_data.time_cost)

    r4_b = aio_canvas_task.push(f'funboost_url_video_b')
    print(r4_b.wait_rpc_data_or_raise(raise_exception=False).to_pretty_json_str())
    print('funboost_url_video_b 下载->转码->通知 耗时', r4_b.rpc_data.time_cost)

    ctrl_c_recv()
