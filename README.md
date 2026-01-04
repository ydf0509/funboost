
# 1. Python 万能分布式函数调度框架 Funboost 简介

**Funboost** 是一个 Python 万能分布式函数调度框架。以下是您的核心学习资源导航：

| 资源类型 | 链接地址 | 说明 |
| :--- | :--- | :--- |
| ⚡ **快速预览** | [👉 点击查看演示](https://ydf0509.github.io/funboost_git_pages/funboost_promo.html) | 直观感受框架运行效果 |
| 📖 **完全教程** | [👉 ReadTheDocs](https://funboost.readthedocs.io/zh-cn/latest/index.html) | 包含原理、API 与进阶用法 |
| 🤖 **AI 助教** | [👉 AI 学习指南](https://funboost.readthedocs.io/zh-cn/latest/articles/c14.html) | **[必读]** 利用 AI 掌握框架的最佳捷径 |


## 1.0 funboost 框架说明介绍

`funboost`是一个 万能 强大 简单  自由 的 `python` 全功能分布式调度框架,它的作用是给用户任意项目的任意函数赋能

**Funboost 的核心价值主张：把复杂留给框架，把简单留给用户。**

<iframe src="https://ydf0509.github.io/funboost_git_pages/index2.html" width="100%" height="2400" style="border:none;"></iframe>


<h4>📹 观看 funboost 视频</h4>
<video controls width="800" 
      src="https://ydf0509.github.io/funboost_git_pages/%E8%A7%86%E9%A2%91-Funboost_%E8%A7%86%E9%A2%91.mp4">
   您的浏览器不支持视频播放。
</video>

<h4>🎧 收听 funboost 音频</h4>
<audio controls 
      src="https://ydf0509.github.io/funboost_git_pages/%E9%9F%B3%E9%A2%91-funboost_%E9%9F%B3%E9%A2%91.mp4">
   您的浏览器不支持音频播放。
</audio>

#### 快速了解和上手funboost，直接看[1.3例子](#13-框架使用例子)


### 1.0.0 funboost 框架安装方式  

```shell
pip install funboost --upgrade  

或 pip install funboost[all]  #一次性安装所有小众三方中间件  
```  


### 1.0.1 funboost 功能作用

- **万能分布式调度**：`funboost` 通过一行 @boost 装饰器，将普通函数瞬间升级为具备 分布式执行、FaaS 微服务化、CDC 事件驱动 能力的超级计算单元，连接一切，调度万物。
- **全能支持**：自动支持 **40+种** 消息队列 + **30+种** 任务控制功能 + `python`中**所有**的并发执行方式。
- **FaaS 能力**：通过 `funboost.faas` 的功能，可以一键快速实现 **FaaS (Function as a Service)**，让函数秒变自动发现的微服务。

- **重功能，轻使用**：
   `funboost` 的功能是**全面性重量级**，用户能想得到的功能 99% 全都有；但使用方式却是**极致轻量级**，只有 `@boost` 一行代码需要写。

- **颠覆性设计**：
   `funboost` 的神奇之处在于它同时拥有“**轻量级使用方式**”和“**重量级功能集**”，完全颠覆了“功能强大=使用复杂”的传统思维。它是对传统 Python 框架设计的一次巧妙超越。
   
   只需要一行 `@boost` 代码即可分布式执行 `python` 一切任意函数，99% 用过 `funboost` 的 `pythoner` 核心感受是：**方便、高速、强大、自由**。  



#### 1.0.1.1 Funboost 的适用场景

`funboost` 是 **Python 函数的万能加速器**。它包罗万象，一统编程思维，将经典的 **生产者 + 消息中间件 + 消费者** 模式封装到了极致。

无论新老项目，Funboost 都能无缝融入，为您提供以下核心能力：

*   🌐 **需要分布式？**
    没问题！Funboost 支持 **40+种** 消息队列中间件。只要是叫得上名字的 MQ（甚至包括数据库、文件系统），它都能支持。

*   ⚡ **需要 FaaS (Function as a Service)？**
    **这是亮点！** 借助 `funboost.faas`，您可以一键将普通函数转化为 HTTP 微服务接口。函数自动发现，发布消息、获取结果、管理任务，瞬间完成 Serverless 般的体验。

*   🚀 **需要并发？**
    满足你！Python 所有的并发模式（**线程、协程、多进程**）任你选择，甚至支持它们**叠加使用**，榨干 CPU 性能。

*   🛡️ **需要可靠性？**
    稳如泰山！**消费确认 (ACK)**、自动重试、死信队列 (DLQ)、断点续爬... 即使服务器宕机，任务也绝不丢失。

*   🎛️ **需要控制力？**
    如臂使指！**精准 QPS 控频**、分布式限流、定时任务、延时任务、超时熔断、任务过滤... 给您三十多种控制武器。

*   📊 **需要监控？**
    一目了然！开箱即用的 **Funboost Web Manager**，让您对任务状态、队列积压、消费者实例等信息了如指掌。

*   🦅 **需要自由？**
    零侵入！它不绑架您的代码，不强管您的项目结构。**随时能用，随时能走**，还您最纯粹的 Python 编程体验。


#### 1.0.1.2 🤔 灵魂发问：Funboost 到底是什么？

**Funboost 的功能已经极其丰富，甚至可以用“功能过剩”或“全能怪兽”来形容。**

> **Funboost 早已超越了“任务队列框架”的传统定义，它已进化为新一代的「泛函计算平台 (Universal Function Computing Platform)」。**
>
> 如果说 Celery 是异步任务的“工具”，那么 Funboost 则是函数计算的“基础设施”。它不仅完美覆盖了 Celery 的核心能力，更打破了技术栈的边界，以**“函数”**为原子核心，贪婪地吞噬并融合了 **FaaS、RPC、微服务架构、网络爬虫、实时数据同步 (CDC/ETL) 、IOT（MQTT）、分布式定时任务、部署、运维；并完整支持 事件驱动 (EDA) 与 全链路可观测性（OpenTelemetry）**。
>
> 在 Funboost 的世界里，不再是对标 Celery，而是重新定义 Python 函数的生产力边界。

> **答**：很难用一句话定义它。Funboost 是一个**万能框架**，几乎覆盖了 Python 所有的编程业务场景。它的答案是发散的，拥有无限可能。

👉 **[点击查看发散性答案 (文档 6.0b 章节)](https://funboost.readthedocs.io/zh-cn/latest/articles/c6.html#b-funboost)**

#### 1.0.1.3 💖 核心关切：值得我投入时间学习吗？

> **答**：**绝对值得**。选择一个用途狭窄、性能平庸、写法受限的框架，确实是在浪费生命。Funboost 则完全不同。

👉 **[查看详细评估报告 (文档 6.0 章节)](https://funboost.readthedocs.io/zh-cn/latest/articles/c6.html#funboost)**


#### 1.0.1.4 Funboost 与 Celery 的理念区别

> **核心比喻**：
> `funboost` 与 `celery` 的关系，如同 **iPhone** 与 **诺基亚塞班**。
> 它们的核心功能虽都是通讯（任务调度），但不能因为功能重叠就判定为重复造轮子。正如 iPhone 重新定义了手机，**Funboost 正在重新定义分布式任务调度，让“框架奴役”成为历史。**

**1. 共同点**
两者本质上都是基于分布式消息队列的异步任务调度框架，遵循经典的编程思想：
*   `生产者 (Producer)` -> `中间件 (Broker)` -> `消费者 (Consumer)`

**2. 核心区别**

| 维度 | **Celery (重型框架)** | **Funboost (函数增强器)** |
| :--- | :--- | :--- |
| **设计理念** | **框架奴役**：代码需围绕 Celery 的架构和 App 实例组织。 | **自由赋能**：非侵入式设计，为任意函数插上分布式的翅膀。 |
| **一等公民** | `Celery App` 实例 (Task 是二等公民) | **用户函数** (无需关注 App 实例) |
| **核心语法** | 需定义 App，使用 `@app.task` | 直接使用 **`@boost`** 装饰器 |
| **易用性** | 需规划特定的项目结构，上手门槛较高。 | 极简，任意位置的新旧函数加上装饰器即可用。 |
| **性能表现** | 传统性能基准。 | **断层式领先**：发布性能是 Celery 的 **22倍**，消费性能是 **46倍**。 |
| **功能广度** | 支持主流中间件。 | 支持 **40+** 种中间件，拥有更多精细的任务控制功能。 |


#### 1.0.1.5 Funboost 支持的并发模式

`funboost` 全面覆盖 Python 生态下的并发执行方式，并支持灵活的组合叠加：

*   **基础并发模式**：支持 `threading` (多线程)、`asyncio` (异步IO)、`gevent` (协程)、`eventlet` (协程) 以及 `单线程` 模式。
*   **叠加增强模式**：支持 **多进程 (Multi-Processing)** 与上述任一细粒度并发模式（如多线程或协程）进行叠加，最大限度利用多核 CPU 资源。

#### 1.0.1.6 Funboost 支持的消息队列中间件 (Broker)

得益于强大的架构设计，在 `funboost` 中 **“万物皆可为 Broker”**。不仅涵盖了传统 MQ，更拓展了数据库、网络协议及第三方框架。

*   **传统消息队列**：RabbitMQ, Kafka, NSQ, RocketMQ, MQTT, NATS, Pulsar 等。
*   **数据库作为 Broker**：
    *   **NoSQL**: Redis (支持 List, Pub/Sub, Stream 等多种模式), MongoDB.
    *   **SQL**: MySQL, PostgreSQL, Oracle, SQL Server, SQLite (通过 SQLAlchemy/Peewee 支持).
*   **网络协议直连**：TCP, UDP, HTTP, gRPC (无需部署 MQ 服务即可实现队列通信)。
*   **文件系统**：本地文件/文件夹, SQLite (适合单机或简单场景).
*   **事件驱动 (CDC)**：支持 **MySQL CDC** (基于 Binlog 变更捕获)，使 Funboost 具备了事件驱动能力，设计理念远超传统任务队列。
*   **第三方框架集成**：可直接将 Celery, Dramatiq, Huey, RQ, Nameko 等框架作为底层 Broker，利用 Funboost 的统一接口调度它们的核心。





#### 1.0.1.7 **funboost 学习难吗?**   
#### 🎓 1.0.1.7 Funboost 学习难吗？

**答案是：极易上手。Funboost 是“反框架”的框架。**

*   🎯 **核心极简**
    整个框架只需要掌握 **`@boost`** 这一个装饰器及其入参（`BoosterParams`）。所有的用法几乎都遵循 **1.3 章节** 示例的模式，一通百通。

*   🛡️ **零代码侵入**
    *   **拒绝“框架奴役”**：不像 `Celery`、`Django` 或 `Scrapy` 那样强迫你按照特定的目录结构组织代码（一旦不用了，代码往往需要大改）。
    *   **即插即用**：Funboost 对你的项目文件结构 **0 要求**，你可以随时将其引入任何新老项目中。

*   🔄 **进退自如（双模运行）**
    即使引入了 Funboost，也不需要担心代码被绑定。加上 `@boost` 装饰器后，你的函数依然保持纯洁：
    *   调用 `fun(x, y)`：**直接运行函数**（同步执行，不经过队列，和没加装饰器一样）。
    *   调用 `fun.push(x, y)`：**发送到消息队列**（分布式异步执行）。

👉 *关于“Funboost 学习和使用难吗？”的详细深度回答，请参阅文档 **`6.0.c`** 章节。*


#### 1.0.1.8 📊 可视化监控与管理
Funboost 内置了强大的 **Funboost Web Manager** 管理系统。
*   **全方位掌控**：支持对任务消费情况进行全面的查看、监控和管理。
*   **开箱即用**：无需额外部署复杂的监控组件，即可掌握队列积压、消费者状态等核心指标。

#### 1.0.1.9 🚀 性能表现：断层式领先
Funboost 的性能与 Celery 相比，有着**数量级**的优势（基于控制变量法测试）：
*   **发布性能**：是 Celery 的 **22倍**。
*   **消费性能**：是 Celery 的 **46倍**。
> *注：详细的控制变量法对比测试报告，请参阅文档 **2.6 章节**。*

#### 1.0.1.10 ⭐ 用户口碑与评价
**95% 的用户**在初步使用后都表示“相见恨晚”。核心评价如下：
*   **极致自由**：Funboost 对用户代码的编程思维**零侵入**。
*   **拒绝改造**：不像其他框架要求用户围绕框架逻辑重构代码，Funboost 尊重用户的原生代码结构。
*   **核心体验**：简单、强大、丰富。

#### 1.0.1.11 📜 历史版本与兼容性
*   **旧框架名称**：`function_scheduling_distributed_framework`
*   **兼容说明**：两者的关系和兼容性详情请见 **1.0.3 章节**。
*   **旧版地址**：[GitHub - distributed_framework](https://github.com/ydf0509/distributed_framework)




## 1.1 📚 核心资源与文档导航

### 1.1.1 📝 项目文档入口

> **🚀 快速上手指南**
>
> *   **文档说明**：文档篇幅较长，主要包含原理讲解与框架对比（`How` & `Why`）。
> *   **学习捷径**：**您只需要重点学习 [1.3 章节] 的这 1 个例子即可！** 其他例子仅是修改 `@boost` 装饰器中 `BoosterParams` 的入参配置。
> *   **核心要点**：`funboost` 极其易用，仅需掌握一行 `@boost` 代码。
> *   **🤖 AI 辅助**：强烈推荐阅读 **[第 14 章]**，学习如何利用 AI 大模型快速掌握 `funboost` 的用法。

**🔗 在线文档地址**：[ReadTheDocs - Funboost Latest](https://funboost.readthedocs.io/zh-cn/latest/index.html)

#### 📖 文档章节速览

| 🔰 基础入门 & 核心概念 | 🚀 进阶功能 & 场景实战 | 🤖 AI 辅助 & 问题排查 |
| :--- | :--- | :--- |
| [1. funboost 框架简介](https://funboost.readthedocs.io/zh-cn/latest/articles/c1.html) | [4b. 代码示例 (**高级进阶**)](https://funboost.readthedocs.io/zh-cn/latest/articles/c4b.html) | [**14. AI 辅助学习指南 (必读)**](https://funboost.readthedocs.io/zh-cn/latest/articles/c14.html) |
| [2. funboost 对比 Celery](https://funboost.readthedocs.io/zh-cn/latest/articles/c2.html) | [8. 爬虫实战：自由编程 vs 框架奴役](https://funboost.readthedocs.io/zh-cn/latest/articles/c8.html) | [6. 常见问题 Q&A](https://funboost.readthedocs.io/zh-cn/latest/articles/c6.html) |
| [3. 框架详细介绍](https://funboost.readthedocs.io/zh-cn/latest/articles/c3.html) | [9. 轻松远程服务器部署](https://funboost.readthedocs.io/zh-cn/latest/articles/c9.html) | [10. 常见报错与问题反馈](https://funboost.readthedocs.io/zh-cn/latest/articles/c10.html) |
| [4. **各种代码示例 (核心)**](https://funboost.readthedocs.io/zh-cn/latest/articles/c4.html) | [11. 集成第三方框架 (Celery/Kombu等)](https://funboost.readthedocs.io/zh-cn/latest/articles/c11.html) | [7. 更新记录](https://funboost.readthedocs.io/zh-cn/latest/articles/c7.html) |
| [5. 运行时截图展示](https://funboost.readthedocs.io/zh-cn/latest/articles/c5.html) | [12. 命令行控制台支持](https://funboost.readthedocs.io/zh-cn/latest/articles/c12.html) | [20. Gemini AI 生成的框架中心思想](https://funboost.readthedocs.io/zh-cn/latest/articles/c20.html) |
| | [13. Web Manager 可视化管理](https://funboost.readthedocs.io/zh-cn/latest/articles/c13.html) | |
| | [⚡ **15. FaaS Serverless 微服务 (战略级核心)**](https://funboost.readthedocs.io/zh-cn/latest/articles/c15.html) | |

---

### 1.1.2 📦 源码与依赖

*   **GitHub 项目主页**：[ydf0509/funboost](https://github.com/ydf0509/funboost)
*   **nb_log 日志文档**：[NB-Log Documentation](https://nb-log-doc.readthedocs.io/zh_CN/latest/articles/c9.html#id2)
   
---

## 1.2 框架功能介绍  

有了 `funboost`，开发者将获得“上帝视角”的调度能力：
*   🚫 **告别繁琐**：无需亲自手写进程、线程、协程的底层并发代码。
*   🔌 **万能连接**：无需亲自编写操作 `Redis`、`RabbitMQ`、`Kafka`、`Socket` 等中间件的连接代码。
*   🧰 **全能控制**：直接拥有 30+ 种企业级任务控制功能。

**funboost示图：**  
![funboost示图](https://s21.ax1x.com/2024/04/29/pkFFghj.png)


**也就是这种非常普通的流程图,一样的意思**  
![funboost示图](https://s21.ax1x.com/2024/04/29/pkFFcNQ.png)

### 1.2.1 🆚 对比：Funboost 取代传统线程池

以下两种方式均实现 **10并发** 运行函数 `f`。Funboost 更加简洁且具备扩展性。

#### ❌ 方式 A：手动开启线程池 (传统)
```python
import time
from concurrent.futures import ThreadPoolExecutor

def f(x):
    time.sleep(3)
    print(x)

pool = ThreadPoolExecutor(10)

if __name__ == '__main__':
    for i in range(100):
        pool.submit(f, i)
```

#### ✅ 方式 B：Funboost 模式 (推荐)
```python
import time
from funboost import BoosterParams, BrokerEnum

# 仅需一行装饰器，即可获得 10 线程并发 + 消息队列能力
@BoosterParams(queue_name="test_insteda_thread_queue", 
               broker_kind=BrokerEnum.MEMORY_QUEUE, 
               concurrent_num=10, 
               is_auto_start_consuming_message=True)
def f(x):
    time.sleep(3)
    print(x)

if __name__ == '__main__':
    for i in range(100):
        f.push(i)
```

### 1.2.2 🚀 强大的任务控制功能矩阵

Funboost 不仅仅是任务队列，它是一个全功能的任务调度平台。

#### 🌐 分布式与中间件
*   **多中间件支持**：支持 40+ 种中间件（Redis, RabbitMQ, Kafka, RocketMQ, SQL, 文件等）。
*   **任务持久化**：依托中间件特性，天然支持任务持久化存储。

#### ⚡ 并发与性能
*   **全模式并发**：支持 `Threading`、`Gevent`、`Eventlet`、`Asyncio`、`Single_thread`。
*   **多进程叠加**：支持在以上 5 种模式基础上叠加 **多进程**，榨干多核 CPU 性能。

#### 🕹️ 流量与频率控制
*   **精准控频 (QPS)**：精确控制每秒运行次数（如 0.02次/秒 或 50次/秒），无视函数耗时波动。
*   **分布式控频**：在多机、多容器环境下，严格控制全局总 QPS。
*   **暂停/恢复**：支持从外部动态暂停或继续消费。

#### 🛡️ 可靠性与容错
*   **断点接续**：无惧断电或强制杀进程，依赖 **ACK 消费确认机制**，确保任务不丢失。
*   **自动重试**：函数报错自动重试指定次数。
*   **死信队列**：重试失败或主动抛出异常的消息自动进入 DLQ (Dead Letter Queue)。
*   **重新入队**：支持主动将消息重新放回队列头部。

#### ⏰ 调度与时效
*   **定时任务**：基于 `APScheduler`，支持间隔、CRON 等多种定时触发。
*   **延时任务**：支持任务发布后延迟 N 秒执行。
*   **时间窗口**：支持指定某些时间段（如白天）不运行任务。
*   **超时熔断**：函数运行超时自动 Kill。
*   **过期丢弃**：支持设置消息有效期，过期未消费自动丢弃。

#### 📊 监控与运维
*   **可视化 Web**：自带 Web 管理界面，查看队列状态、消费速度。
*   **五彩日志**：集成 `nb_log`，提供多进程安全的切割日志与控制台高亮显示。
*   **全链路追踪**：支持记录任务入参、结果、耗时、异常信息并持久化到 MongoDB/MySQL。
*   **RPC 模式**：发布端可同步等待消费端的返回结果。
*   **远程部署**：一行代码将函数自动部署到远程 Linux 服务器。
*   **命令行 CLI**：支持通过命令行管理任务。

> **🏆 稳定性承诺**
>
> 能够直面百万级 C 端用户业务（App/小程序），连续 3 个季度稳定运行无事故。
> **0 假死、0 崩溃、0 内存泄漏**。
> Windows 与 Linux 行为 100% 一致（解决了 Celery 在 Windows 下的诸多痛点）。


## 1.3 🚀 快速上手：你的第一个 Funboost 程序

> **⚠️ 环境准备 (重要)**
>
> 在运行代码前，请确保您了解 **`PYTHONPATH`** 的概念。
> Windows cmd 或 Linux 运行时，建议将 `PYTHONPATH` 设置为项目根目录，以便框架自动生成或读取配置。
> 👉 [点击学习 PYTHONPATH](https://github.com/ydf0509/pythonpathdemo)

### 1.3.1 ✨ Hello World：最简单的任务调度

这个例子演示了如何将一个普通的求和函数变成分布式任务。

**代码逻辑说明：**
1.  **定义任务**：使用 `@boost` 装饰器，指定队列名 `task_queue_name1` 和 QPS `5`。
2.  **发布任务**：调用 `task_fun.push(x, y)` 发送消息。
3.  **消费任务**：调用 `task_fun.consume()` 启动后台线程自动处理。

```python
import time
from funboost import boost, BrokerEnum, BoosterParams

# 核心配置：使用本地 SQLite 作为消息队列，QPS 限制为 5
@boost(BoosterParams(
    queue_name="task_queue_name1", 
    qps=5, 
    broker_kind=BrokerEnum.SQLITE_QUEUE
))
def task_fun(x, y):
    print(f'{x} + {y} = {x + y}')
    time.sleep(3)  # 模拟耗时，框架会自动并发绕过阻塞

if __name__ == "__main__":
    # 1. 生产者：发布 100 个任务
    for i in range(100):
        task_fun.push(i, y=i * 2)
    
    # 2. 消费者：启动循环调度
    task_fun.consume()
```

> **💡 Tips**
> 如果在 Linux/Mac 上使用 `SQLITE_QUEUE` 报错 `read-only`，请在 `funboost_config.py` 中修改 `SQLLITE_QUEUES_PATH` 为有权限的目录（详见文档 10.3）。

**运行效果截图：**

**发布任务截图：**
![发布截图](https://s21.ax1x.com/2024/04/29/pkFkP4H.png) 

**消费任务截图：**
![消费截图](https://s21.ax1x.com/2024/04/29/pkFkCUe.png)



### 1.3.2 🔥 进阶实战：RPC、定时任务与丝滑连招

这是一个集大成的例子，展示了 Funboost 的核心能力：
*   ✅ **参数复用**：继承 `BoosterParams` 减少重复代码。
*   ✅ **RPC 模式**：发布端同步获取消费结果。
*   ✅ **丝滑启动**：非阻塞连续启动多个消费者。
*   ✅ **定时任务**：基于 `APScheduler` 的强大定时能力。

```python
import time
from funboost import boost, BrokerEnum, BoosterParams, ctrl_c_recv, ConcurrentModeEnum, ApsJobAdder

# 1. 定义公共配置基类，减少重复代码
class MyBoosterParams(BoosterParams):
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
    max_retry_times: int = 3
    concurrent_mode: str = ConcurrentModeEnum.THREADING 

# 2. 消费函数 step1：演示 RPC 模式
@boost(MyBoosterParams(
    queue_name='s1_queue', 
    qps=1,   
    is_using_rpc_mode=True  # 开启 RPC，支持获取结果
))
def step1(a: int, b: int):
    print(f'step1: a={a}, b={b}')
    time.sleep(0.7)
    # 函数内部可以继续发布任务给 step2
    for j in range(10):
        step2.push(c=a+b+j, d=a*b+j, e=a-b+j)
    return a + b

# 3. 消费函数 step2：演示参数覆盖
@boost(MyBoosterParams(
    queue_name='s2_queue', 
    qps=3, 
    max_retry_times=5  # 覆盖基类默认值
)) 
def step2(c: int, d: int, e: int=666):
    time.sleep(3)
    print(f'step2: c={c}, d={d}, e={e}')
    return c * d * e

if __name__ == '__main__':
    # --- 启动消费 ---
    step1.consume()  # 非阻塞启动
    step2.consume()
    step2.multi_process_consume(3) # 叠加 3 个进程并发

    # --- RPC 调用演示 ---
    async_result = step1.push(100, b=200)
    print('RPC 结果：', async_result.result)  # 阻塞等待结果

    # --- 批量发布演示 ---
    for i in range(100):
        step1.push(i, i*2)
        # publish 方法支持更多高级参数（如 task_id）
        step1.publish({'a':i, 'b':i*2}, task_id=f'task_{i}')

    # --- 定时任务演示 (APScheduler) ---
    # 方式1：指定日期执行
    ApsJobAdder(step2, job_store_kind='redis', is_auto_start=True).add_push_job(
        trigger='date', run_date='2025-06-30 16:25:40', args=(7, 8, 9), id='job1'
    )
    # 方式2：间隔执行
    ApsJobAdder(step2, job_store_kind='redis').add_push_job(
        trigger='interval', seconds=30, args=(4, 6, 10), id='job2'
    )

    # 阻塞主线程，保持程序运行
    ctrl_c_recv()
```

> **🧠 设计哲学**
> Funboost 提倡 **“反框架”** 思维：你才是主角，框架只是插件。
> `task_fun(1, 2)` 是直接运行函数，`task_fun.push(1, 2)` 才是发布到队列。
> 随时可以拿掉 `@boost`，代码依然是纯粹的 Python 函数。

---

### 1.3.3 ✂️ 极简写法：省略 `@boost`

如果你追求极致简洁，也可以直接使用 `@BoosterParams` 作为装饰器，效果等同于 `@boost(BoosterParams(...))`。

```python
# 极简写法
@BoosterParams(queue_name="task_queue_simple",qps=5)
def task_fun(a, b):
    return a + b
```

### 1.3.4 ❌ 过时写法： 直接在 @boost传各种配置入参，不推荐
这种直接在 `@boost`传参，而不使用 `BoosterParams`来传各种配置，是过气写法不推荐，因为不能代码补全了。   
```python
# ⚠️ 反例：过时写法，不推荐！
@boost(queue_name="task_queue_simple",qps=5)
def task_fun(a, b):
    return a + b
```


## 🖥️ Funboost Web Manager 界面预览

可视化管理后台提供了强大的监控与运维能力，以下是核心功能截图：



函数消费结果：可查看和搜索函数实时消费状态和结果  
[![函数结果表](https://s41.ax1x.com/2025/12/19/pZ1L5h4.png)](https://imgchr.com/i/pZ1L5h4)

队列操作：查看和操作队列，包括清空、暂停消费、恢复消费、调整QPS和并发  
[![队列操作1](https://s41.ax1x.com/2025/12/17/pZlrYPH.png)](https://imgchr.com/i/pZlrYPH)
[![队列操作2](https://s41.ax1x.com/2025/12/17/pZlrUxI.png)](https://imgchr.com/i/pZlrUxI)

队列操作：查看消费曲线图，查看各种消费指标（历史运行次数、失败次数、近10秒完成/失败、平均耗时、剩余消息数量等）  
[![队列消费曲线](https://s41.ax1x.com/2025/12/19/pZ104HS.png)](https://imgchr.com/i/pZ104HS) 

RPC调用：在网页上对30种消息队列发布消息并获取函数执行结果；可根据task_id获取结果  
[![rpc调用成功-绿色](https://s41.ax1x.com/2025/12/19/pZ10RjP.png)](https://imgchr.com/i/pZ10RjP)

定时任务管理：列表页  
[![定时任务列表](https://s41.ax1x.com/2025/12/17/pZlrNRA.png)](https://imgchr.com/i/pZlrNRA)



## 1.4 💡 为什么 Python 极其需要分布式函数调度？

Python 语言的特性决定了它比 Java/Go 等语言更依赖分布式调度框架。主要原因有两点：

### 1️⃣ 痛点一：GIL 锁的限制 (多核利用率低)
> 🛑 **现状**：由于 GIL (全局解释器锁) 的存在，普通的 Python 脚本无法利用多核 CPU。在 16 核机器上，CPU 利用率最高只能达到 **6.25% (1/16)**。
> 😓 **难点**：手动编写 `multiprocessing` 多进程代码非常麻烦，涉及复杂的进程间通信 (IPC)、任务分配和状态共享。

✅ **Funboost 的解法**：
*   **天生解耦**：利用中间件（如 Redis/RabbitMQ）解耦任务,无法手写怎么给多进程分配任务和进程间通信。
*   **无感多进程**：单进程脚本与多进程脚本写法完全一致，**无需**手写 `multiprocessing`，自动榨干多核性能。

### 2️⃣ 痛点二：原生性能瓶颈 (动态语言特性)
> 🐌 **现状**：作为动态语言，Python 的单线程执行速度通常慢于静态语言。
> 🚀 **需求**：为了弥补单机速度，必须通过**横向扩展**来换取时间。

✅ **Funboost 的解法**：
*   **无缝扩展**：代码无需任何修改，即可适应多种运行环境：
    *   🔄 **多解释器**：同一台机器启动多个 Python 进程。
    *   🐳 **容器化**：部署在多个 Docker 容器中。
    *   ☁️ **跨物理机**：部署在多台物理服务器上。
*   **统一驱动**：Funboost 作为调度核心，让 Python 跑在集群之上，获得媲更高的系统吞吐量。


## 1.5 🎓 最佳学习路径

Funboost 的设计哲学是 **“极简主义”**。您无需阅读长篇大论，只需通过实践掌握核心：

1.  **🧪 实验式学习**：
    *   以 **1.3 章节** 的求和代码为蓝本。
    *   修改 `@boost` 装饰器中的参数（如 `qps`、`concurrent_num`）。
    *   在函数中添加 `time.sleep()` 模拟耗时。
    *   **观察**：观察控制台输出，体会分布式、并发和控频的实际效果。

2.  **✨ 一行代码原则**：
    *   这是最简单的框架：核心只有一行 `@boost` 代码。
    *   如果您能掌握这个装饰器，就掌握了整个框架。这比学习那些需要继承多个类、配置多个文件的传统框架要简单得多。

> **🤖 AI 助教**
> 强烈推荐参考 **[文档第 14 章]**，学习如何利用 AI 大模型快速精通 `funboost` 的各种高级用法。

---

## 1.6 🥋 funboost 练就吸星大法神功，一招吸走 Celery 毕生内力

**Funboost 的极简招式 + Celery 的深厚内力 = 独步武林**

> “江湖中人多迷信 Celery 的名门光环，虽 Funboost 身法快过其数十倍，且有演武场（2.6章节）实测为证，奈何部分豪杰固步自封，不愿亲自试剑。
> Funboost 遂施展 **‘吸星大法’**，将 Celery 纳为己用（作为 Broker）。**既入我门，便由我控**，以此化解众生执念。”

Celery 称霸 Python 异步江湖十数载，内力虽深厚，但其招式繁复、门规森严（配置繁琐），令无数豪杰望而却步。 
今 Funboost 施展 **“吸星大法”**，只需一招 `BrokerEnum.CELERY`，顷刻间将 Celery 化为 **座下护法**。自此，Celery 竟成 Funboost 之一大 **子集**，听凭号令！ 

### ⚔️ 降维打击：化繁为简的绝世武功
通过 Funboost 驾驭 Celery，犹如令狐冲习得独孤九剑，破尽天下繁琐招式，直击要害：

| 🆚 招式对决 | 🛑 原生 Celery (旧派宗门的桎梏) | 🟢 Funboost 御剑术 (新派宗师的洒脱) |
| :--- | :--- | :--- |
| **启动法门**<br>(部署) | **念诵咒语**：需死记硬背 `worker/beat` 等冗长命令行，稍有错漏便走火入魔。 | **意念合一**：代码即启动，无需记忆任何咒语，`python xx.py` 一剑破万法。 |
| **门派规矩**<br>(结构) | **清规戒律**：强行规定目录结构，错置文件即被逐出师门，极其僵化。 | **无招胜有招**：飞花摘叶皆可伤人，任意目录、任意文件皆可为战场，毫无束缚。 |
| **心法运转**<br>(门槛) | **经脉逆行**：需手动修炼 `includes` 和 `task_routes`，极易气血翻涌（配置报错）。 | **浑然天成**：自动打通任督二脉，框架自动发现并注册任务，行云流水。 |
| **洞察天地**<br>(体验) | **盲人摸象**：`@app.task` 入参如雾里看花，IDE 无法感知，极易行差踏错。 | **天眼通**：`BoosterParams` 开启全知视角，代码补全如神助，所见即所得。 |

> **📜 藏经阁 (代码示例)**
> 欲练此功，请翻阅 **[11.1 章节]**。
> 您只需施展 Funboost 的极简剑法，底层那拥有万钧之力的 Celery 引擎便会自动为您移山填海，虽有雷霆之威，却无反噬之虞。


 需要说明的是，funboost性能是已经远超celery，吸纳celery作为broker，兼容celery作为funboost的broker，是为了打消有的人对funboost的调度核心的稳定性的疑虑。   
 > 你可以看文档2.6章节**funboost vs celery控制变量法性能对比**，以及2.9章节，**funboost到底为什么性能比celery高几十倍？太离谱了,太假了是吗？**


[查看分布式函数调度框架完整文档](https://funboost.readthedocs.io/)  

![](https://visitor-badge.glitch.me/badge?page_id=distributed_framework)  

<div> </div>  

[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  

