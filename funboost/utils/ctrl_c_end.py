import os
import sys
import time
import signal


def signal_handler(signum, frame):
    print(f'收到信号 {signum}，程序准备退出', flush=True)
    sys.exit(4)
    os._exit(44)



def ctrl_c_recv(confirmation_count=1):
    """ 
    程序最末尾加 ctrl_c_recv() 主要是为了主线程持续在运行，方便你敲击键盘 ctrl + c 可以停止程序而已。  
    你即使程序最末尾不加 ctrl_c_recv(),funboost消费程序也会永久持续运行，控制台也会不断打印日志和 `print` 输出。
    
    
    加与不加的详细区别，可以看教程6.25b章节 `## 6.25b `ctrl_c_recv` 到底要不要加？—— 直接看效果`
    
    
    你也可以不用ctrl_c_recv(),  直接在你的启动脚本文件的最末尾加上：
    while 1:
        time.sleep(100) 
    来达到主线程在持续运行的目的。
    """
    # signal.signal(signal.SIGTERM, signal_handler)
    
    for i in range(confirmation_count):
        while 1:
            try:
                time.sleep(2)
            except (KeyboardInterrupt,) as e:
                # time.sleep(2)
                print(f'{type(e)} 你按了ctrl c ,程序退出, 第 {i + 1} 次', flush=True)
                # time.sleep(2)
                break
    # sys.exit(4)
    os._exit(44)
    # exit(444)
