import os
import sys
import time
import signal


def signal_handler(signum, frame):
    print(f'收到信号 {signum}，程序准备退出', flush=True)
    sys.exit(4)
    os._exit(44)


def ctrl_c_recv():
    """ 
    主要目的就是阻止主线程退出而已。 因为funboost为了方便用户连续启动多个consume都是子线程运行循环调度的。
    apscheduler background 类型必须有主线程在运行，否则会很快结束。所以需要阻止主线程退出。
    在代码最最末尾加上 ctrl_c_recv() 就可以阻止主线程退出。
    
    你也可以直接在你的启动脚本的最末尾加上：
    while 1:
        time.sleep(100) 
    来达到阻止主线程退出的目的。
    """
    # signal.signal(signal.SIGTERM, signal_handler)
    
    for i in range(3):
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
