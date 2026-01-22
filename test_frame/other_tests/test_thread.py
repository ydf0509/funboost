import threading
import time

def worker():  # 非守护线程
    while True:
        print("Worker running...")
        time.sleep(1)

def daemon_worker():  # 守护线程
    while True:
        print("Daemon running...")
        time.sleep(1)

if __name__ == '__main__':
    # 启动非守护线程 (默认 daemon=False)
    t1 = threading.Thread(target=worker)
    t1.start()
    
    # 启动守护线程
    t2 = threading.Thread(target=daemon_worker, daemon=True)
    t2.start()
    
    print("主线程结束")