# -*- coding: utf-8 -*-
"""
Funboost Workflow 示例 - 视频处理 Pipeline

演示使用 chain + chord 实现经典的视频处理工作流：
1. 下载视频
2. 并行转码为多种分辨率
3. 汇总结果并发送通知

这是 Celery Canvas 的经典用例，用 Funboost Workflow 实现。

运行方式：
    cd d:\\codes\\funboost
    D:\\ProgramData\\Miniconda3\\envs\\py39b\\python.exe funboost/workflow/examples/video_pipeline.py
"""

import time
import typing

from funboost import boost, ctrl_c_recv, BrokerEnum, fct
from funboost.workflow import chain, group, chord, WorkflowBoosterParams


# ============================================================
# 定义工作流任务
# ============================================================

class VideoWorkflowParams(WorkflowBoosterParams):
    """视频处理工作流的公共参数"""
    broker_kind: str = BrokerEnum.SQLITE_QUEUE
    broker_exclusive_config: dict = {'pull_msg_batch_size': 1}
    max_retry_times: int = 0


@boost(VideoWorkflowParams(queue_name='wf_download_video'))
def download_video(url: str) -> str:
    """
    步骤1：下载视频
    
    :param url: 视频 URL
    :return: 下载后的本地文件路径
    """
    fct.logger.info(f'📥 开始下载视频: {url}')
    
    # 模拟下载耗时
    time.sleep(2)
    
    file_path = f'/downloads/{url.replace("://", "_").replace("/", "_")}'
    fct.logger.info(f'✅ 下载完成: {file_path}')
    
    return file_path


@boost(VideoWorkflowParams(queue_name='wf_transform_video'))
def transform_video(video_file: str, resolution: str = '360p') -> str:
    """
    步骤2：转码视频
    
    :param video_file: 输入视频文件路径
    :param resolution: 目标分辨率
    :return: 转码后的文件路径
    """
    fct.logger.info(f'🔄 开始转码: {video_file} -> {resolution}')
    
    # 模拟转码耗时
    time.sleep(3)
    
    output_file = f'{video_file}_{resolution}.mp4'
    fct.logger.info(f'✅ 转码完成: {output_file}')
    
    return output_file


@boost(VideoWorkflowParams(queue_name='wf_send_finish_msg'))
def send_finish_msg(video_list: typing.List[str], url: str) -> str:
    """
    步骤3：发送完成通知
    
    :param video_list: 转码后的视频文件列表
    :param url: 原始视频 URL
    :return: 完成消息
    """
    fct.logger.info('📧 发送完成通知...')
    fct.logger.info(f'   原始视频: {url}')
    fct.logger.info(f'   转码结果: {video_list}')
    
    # 模拟发送通知
    time.sleep(1)
    
    msg = f'🎉 视频处理完成！{url} -> {len(video_list)} 个分辨率版本'
    fct.logger.info(f'✅ {msg}')
    
    return msg


# ============================================================
# 工作流编排
# ============================================================

def create_video_pipeline(url: str):
    """
    创建视频处理工作流
    
    等价于 Celery Canvas:
    ```python
    chain(
        download_video.s(url),
        chord(
            group(transform_video.s(r) for r in ['360p', '720p', '1080p']),
            send_finish_msg.s(url=url)
        )
    )
    ```
    
    注意：导入 funboost.workflow 后，所有 @boost 装饰的函数自动拥有 .s() 和 .si() 方法
    无需手动添加！
    """
    # 定义工作流
    resolutions = ['360p', '720p', '1080p']
    
    workflow = chain(
        download_video.s(url),
        chord(
            group(transform_video.s(resolution=r) for r in resolutions),
            send_finish_msg.s(url=url)
        )
    )
    
    return workflow


# ============================================================
# 主程序
# ============================================================

if __name__ == '__main__':
    print('=' * 60)
    print('🎬 Funboost Workflow 示例 - 视频处理 Pipeline')
    print('=' * 60)
    
    # 启动消费者
    print('\n📡 启动消费者...')
    download_video.consume()
    transform_video.consume()
    send_finish_msg.consume()
    
    # 等待消费者就绪
    time.sleep(3)
    
    # 创建并执行工作流
    print('\n🚀 执行视频处理工作流...')
    print('-' * 60)
    
    url = 'https://example.com/video.mp4'
    workflow = create_video_pipeline(url)
    
    # 同步执行工作流
    rpc_data = workflow.apply()
    
    print('-' * 60)
    print('\n🏁 工作流执行完成！')
    print(f'   最终结果: {rpc_data}')
    print('=' * 60)
    
    # 保持运行
    ctrl_c_recv()
