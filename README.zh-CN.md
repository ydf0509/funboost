<div align="center">
  <h1>FunBoost</h1>
  <span><a href="./README.md">English</a> | 中文</span>
</div>

## ⚡ 简介

**Funboost是一个Python函数加速器和分布式调度框架，具有以下特点：**

- 全面性功能：几乎涵盖所有用户可能需要的功能。
- 轻量级使用：仅需一行@boost代码即可实现分布式执行。
- 广泛支持：支持Python所有并发模式，兼容全球知名消息队列中间件。
- 框架兼容性：支持Celery等任务队列框架，简化配置和调度。
- 编程思维统一：兼容50%的Python编程业务场景。
- 强大功能：支持5种并发模式，30+种消息队列，30种任务控制功能。
- 简单学习曲线：只需学习一个装饰器@boost。
- 无代码入侵：可以轻松添加到任何现有项目，不影响项目结构。
- 灵活应用：用户可以随时引入或移除Funboost，无需改变代码组织。

## 📚 文档

- FunBoost官方文档: [链接](https://funboost.readthedocs.io/zh-cn/latest/index.html)
- NbLog官方文档：[链接](https://nb-log-doc.readthedocs.io/zh-cn/latest/articles/c9.html#id2)

## 🚀 快速开始

```sh
pip install funboost --upgrade
```
或者，您可以一次性安装所有小众三方中间件

```sh
pip install funboost[all]  
```

### 运行FunBoost

使用之前先学习 PYTHONPATH的概念 https://github.com/ydf0509/pythonpathdemo
win cmd和linux 运行时候，设置 PYTHONPATH 为项目根目录，是为了自动生成或读取到项目根目录下的 funboost_config.py文件作为配置。

要开始使用 Funboost，你只需要掌握一个关键的例子，即[官方文档](https://funboost.readthedocs.io/zh-cn/latest/articles/c1.html#id9)中的 1.3 节。通过修改 @boost 装饰器的参数，你可以实现各种任务控制功能。
```python
import time
from funboost import boost, BrokerEnum,BoosterParams

# BoosterParams 代码自动补全请看文档4.1.3
@boost(BoosterParams(queue_name="task_queue_name1", qps=5, broker_kind=BrokerEnum.SQLITE_QUEUE))  # 提供20种入参选项，覆盖广泛的运行控制需求。
def task_fun(x, y):
    print(f'{x} + {y} = {x + y}')
    time.sleep(3) # 框架能自动调节并发量，确保task_fun函数每秒稳定执行5次，无视内部耗时。


if __name__ == "__main__":
    for i in range(100):
        task_fun.push(i, y=i * 2)  # 发布者发布任务
    task_fun.consume()  # 消费者启动循环调度并发消费任务
```
### 核心流程

Funboost 框架通过以下两步实现任务的发布和消费：

1. 发布（推送）：

   task_fun.push(1, y=2) 将参数 {"x": 1, "y": 2} 发送到消息队列
   task_queue_name1 中。

2. 消费：

   task_fun.consume() 从消息队列中拉取消息，并发地执行函数 
   
   task_fun(**{"x": 1, "y": 2})，每秒执行5次。

### 配置
   配置文件：首次运行时，框架会在项目根目录生成 funboost_config.py 文件，用户需要根据需求配置消息中间件的 IP、端口、密码等信息。


## 🔧说明

   发布和消费分离：通常，任务发布和任务消费是分离的，不需要位于同一个脚本中。

   中间件解耦：通过消息中间件实现发布和消费的解耦，确保消息的持久化和异步处理。

   学习曲线平缓：用户只需掌握一个核心示例，其他示例主要是参数的调整。

   参数详细解释：@boost 装饰器的参数已经详细解释，简化了学习过程。


### 分布式函数执行的重要性

Python 程序特别需要分布式函数调度框架，原因有二：

GIL 限制：Python 的全局解释器锁限制了多核处理器的 CPU 使用率，通常不超过 100%。
性能问题：Python 作为动态语言，性能普遍低于静态语言。分布式执行可以跨多个进程、容器、物理机提升性能。
分布式函数调度框架简化了多进程编程，提高了 Python 程序的执行效率。

### 框架学习方式

通过修改 @boost 装饰器的参数和函数中的 sleep 时长，反复测试简单的求和示例，可以快速掌握框架的分布式、并发和控频特性。Funboost 框架简单易学，仅需理解一个核心装饰器的使用。

### Funboost 对 Celery 的支持

从 2023 年 4 月起，Funboost 支持将 Celery 作为其 broker，简化了 Celery 的操作：


用户无需直接操作 Celery，无需记忆复杂的命令行和配置。
Funboost 允许用户以简单的语法操控 Celery，自动处理目录结构和任务路由配置。
Funboost 的这种设计，不仅简化了分布式任务的调度，还使得 Python 程序能够更容易地实现高性能计算。



## ✔️ 运行截图

<a href="https://imgse.com/i/pkFkP4H"><img src="https://s21.ax1x.com/2024/04/29/pkFkP4H.png" alt="pkFkP4H.png" border="0" /></a>


<a href="https://imgse.com/i/pkFkCUe"><img src="https://s21.ax1x.com/2024/04/29/pkFkCUe.png" alt="pkFkCUe.png" border="0" /></a>

<a href="https://imgse.com/i/pkE6IYR"><img src="https://s21.ax1x.com/2024/05/07/pkE6IYR.png" alt="pkE6IYR.png" border="0" /></a>

## 💕 感谢 Star

项目获取 star 不易，如果你喜欢这个项目的话，欢迎支持一个 star！这是作者持续维护的唯一动力

[![Star History Chart](https://api.star-history.com/svg?repos=ydf0509/funboost&type=Date)](https://star-history.com/#ydf0509/funboost&Date)