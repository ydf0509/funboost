
import  nb_log

from apscheduler.schedulers.background import BackgroundScheduler
import time

def my_job():
    print("Job executed!")

# 创建调度器
scheduler = BackgroundScheduler()



# 添加任务
scheduler.add_job(my_job, 'interval', seconds=1)
# 启动调度器
scheduler.start(paused=True)

while 1:
    try:
        print("Scheduler is running. Pausing for 10 seconds...")
        time.sleep(10)  # 运行 10 秒

        # 恢复调度器
        scheduler.resume()
        print("Scheduler resumed.")

        time.sleep(10)  # 暂停 10 秒

        # 暂停调度器
        scheduler.pause()
        print("Scheduler paused.")



    except (KeyboardInterrupt, SystemExit):
        # 停止调度器
        scheduler.shutdown()
        print("Scheduler shutdown.")


