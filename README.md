<div align="center">
  <h1>FunBoost</h1>
  <span>English | <a href="./README.zh-CN.md">中文</a></span>
</div>

## ⚡ Introduction

**FunBoost is a Python function accelerator and distributed scheduling framework with the following features:**

- Comprehensive functionality: Covers almost all features that users may need.
- Lightweight usage: Distributed execution can be achieved with just one line of @boost code.
- Wide support: Supports all Python concurrency modes and is compatible with globally renowned message queue middleware.
- Framework compatibility: Supports task queue frameworks such as Celery, simplifying configuration and scheduling.
- Unified programming thinking: Compatible with 50% of Python programming business scenarios.
- Powerful features: Supports 5 concurrency modes, 30+ message queues, and 30 task control features.
- Simple learning curve: Only one decorator @boost needs to be learned.
- Non-invasive code: Can be easily added to any existing project without affecting the project structure.
- Flexible application: Users can introduce or remove FunBoost at any time without changing the code organization.

## 📚 Documentation

- FunBoost Official Documentation: [Link](https://funboost.readthedocs.io/zh-cn/latest/index.html) 
- NbLog Official Documentation: [Link](https://nb-log-doc.readthedocs.io/zh-cn/latest/articles/c9.html#id2) 

## 🚀 Quick Start

```sh
pip install funboost --upgrade
```
Alternatively, you can install all niche third-party middleware at once

```sh
pip install funboost[all]  
```

### Running FunBoost

Before using, learn the concept of PYTHONPATH https://github.com/ydf0509/pythonpathdemo 
When running in win cmd and linux, set PYTHONPATH to the project root directory to automatically generate or read the funboost_config.py file in the project root directory as the configuration.

To start using FunBoost, you just need to master one key example, which is section 1.3 in the [official documentation](https://funboost.readthedocs.io/zh-cn/latest/articles/c1.html#id9). By modifying the parameters of the @boost decorator, you can achieve various task control functions.
```python
import time
from funboost import boost, BrokerEnum,BoosterParams

# BoosterParams code auto-completion see documentation 4.1.3
@boost(BoosterParams(queue_name="task_queue_name1", qps=5, broker_kind=BrokerEnum.SQLITE_QUEUE))  # Provides 20 types of parameters, covering a wide range of operational control needs.
def task_fun(x, y):
    print(f'{x} + {y} = {x + y}')
    time.sleep(3) # The framework can automatically adjust the concurrency to ensure that the task_fun function is executed stably 5 times per second, regardless of the internal time consumption.


if __name__ == "__main__":
    for i in range(100):
        task_fun.push(i, y=i * 2)  # The publisher publishes the task
    task_fun.consume()  # The consumer starts the loop scheduling and consuming tasks concurrently
```

### Core Process

The FunBoost framework implements task publishing and consumption through the following two steps:

1. Publishing (Pushing):

   task_fun.push(1, y=2) sends the parameters {"x": 1, "y": 2} to the message queue
   task_queue_name1.

2. Consumption:

   task_fun.consume() pulls messages from the message queue and executes the function concurrently
   
   task_fun(**{"x": 1, "y": 2}), 5 times per second.

### Configuration
   Configuration file: The first time you run, the framework will generate a funboost_config.py file in the project root directory, where users need to configure the IP, port, password, etc., of the message middleware according to their needs.

## 🔧 Instructions

   Publishing and consumption separation: Usually, task publishing and task consumption are separated and do not need to be in the same script.

   Decoupling through middleware: Achieve decoupling of publishing and consumption through message middleware to ensure the persistence and asynchronous processing of messages.

   Gentle learning curve: Users only need to master one core example, and other examples are mainly adjustments of parameters.

   Detailed parameter explanation: The parameters of the @boost decorator have been explained in detail, simplifying the learning process.

### The Importance of Distributed Function Execution

Python programs especially need a distributed function scheduling framework for two reasons:

GIL Limitation: The Global Interpreter Lock of Python limits the CPU usage of multi-core processors, usually not exceeding 100%.
Performance Issues: As a dynamic language, Python's performance is generally lower than that of static languages. Distributed execution can improve performance by running across multiple processes, containers, and physical machines.
Distributed function scheduling frameworks simplify multi-process programming and improve the execution efficiency of Python programs.

### Framework Learning Method

By modifying the parameters of the @boost decorator and the sleep duration in the function, repeatedly testing the simple addition example can quickly master the framework's distributed, concurrent, and frequency control characteristics. The FunBoost framework is simple and easy to learn, only needing to understand the use of one core decorator.

### FunBoost's Support for Celery

From April 2023, FunBoost supports Celery as its broker, simplifying the operation of Celery:

Users do not need to operate Celery directly, no need to remember complex command lines and configurations.
FunBoost allows users to manipulate Celery with simple syntax, automatically handling directory structure and task routing configuration.
This design of FunBoost not only simplifies the scheduling of distributed tasks but also makes it easier for Python programs to achieve high-performance computing.

## ✔️ Running Screenshot

<a href="https://imgse.com/i/pkFkP4H"><img  src="https://s21.ax1x.com/2024/04/29/pkFkP4H.png"  alt="pkFkP4H.png" border="0" /></a>

<a href="https://imgse.com/i/pkFkCUe"><img  src="https://s21.ax1x.com/2024/04/29/pkFkCUe.png"  alt="pkFkCUe.png" border="0" /></a>

<a href="https://imgse.com/i/pkE6IYR"><img  src="https://s21.ax1x.com/2024/05/07/pkE6IYR.png"  alt="pkE6IYR.png" border="0" /></a>

## 💕 Thanks for the Star

It's not easy for the project to get stars. If you like this project, please support a star! This is the only motivation for the author to maintain it continuously.

[![Star History Chart](https://api.star-history.com/svg?repos=ydf0509/funboost&type=Date)](https://star-history.com/#ydf0509/funboost&Date) 

---
