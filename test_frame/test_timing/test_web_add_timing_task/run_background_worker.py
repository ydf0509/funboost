# run_background_worker.py
import time
from funboost import ApsJobAdder, ctrl_c_recv
from tasks import dynamic_task # 导入任务函数

if __name__ == '__main__':

    print("--- 后台 Worker 和 定时调度器 ---")
    print("正在启动...")

    # 1. 启动消费者，使其开始监听 'web_dynamic_task_queue' 队列
    dynamic_task.consume()
    print("[Worker] 消费者已启动，正在等待任务...")

    # 2. 创建 ApsJobAdder 实例并启动它
    #    - job_store_kind='redis' 确保它能读取到 Web 端添加的计划。
    #    - is_auto_start=True (或不传，默认为True) 会自动启动 apscheduler 的后台调度循环。
    # 这个实例会不断扫描 Redis，发现到期的任务就 push 到消息队列。
    ApsJobAdder(dynamic_task, job_store_kind='redis')
    print("[Scheduler] 定时任务调度器已启动，正在扫描任务计划...")

    print("\n后台服务已准备就绪，按 Ctrl+C 退出。")
    ctrl_c_recv()
