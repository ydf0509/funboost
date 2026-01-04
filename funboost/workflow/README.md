# Funboost Workflow - 声明式任务编排

> 类似 Celery Canvas 的声明式任务编排 API，让工作流定义更简洁直观。

## 🚀 快速开始

```python
from funboost import boost
from funboost.workflow import chain, group, chord, WorkflowBoosterParams

# 1. 使用 WorkflowBoosterParams 定义任务
@boost(WorkflowBoosterParams(queue_name='download_task'))
def download(url):
    return f'/downloads/{url}'

@boost(WorkflowBoosterParams(queue_name='process_task'))
def process(file_path, resolution='360p'):
    return f'{file_path}_{resolution}'

@boost(WorkflowBoosterParams(queue_name='notify_task'))
def notify(results, url):
    return f'完成: {url} -> {results}'

# 2. 构建工作流（声明式）
workflow = chain(
    download.s('video.mp4'),
    chord(
        group(process.s(resolution=r) for r in ['360p', '720p', '1080p']),
        notify.s(url='video.mp4')
    )
)

# 3. 执行
result = workflow.apply()
```

## 更多详情，详见funboost 教程 4b.8 章节 ，**funboost 声明式任务编排 workfolw**