# -*- coding: utf-8 -*-
"""
临时手搞批量聚合 - 不封装，不使用 funboost

这是很多开发者在没有 funboost 时的真实写法：
直接在业务代码里临时搞一堆全局变量、锁、线程...

看看有多乱、多容易出 bug。
"""

import threading
import time
from queue import Queue

# ============================================================
# 你的业务代码里突然多了一堆全局变量...
# ============================================================

# 全局缓冲区（你得自己维护）
_buffer = []

# 全局锁（你得自己加）
_lock = threading.Lock()

# 上次刷新时间（你得自己记）
_last_flush_time = time.time()

# 配置（硬编码在这里，改起来麻烦）
BATCH_SIZE = 10
BATCH_TIMEOUT = 3.0

# 控制后台线程的标志
_running = True


def batch_insert_to_db(items):
    """假装这是你的批量插入函数"""
    print(f"{time.strftime('%H:%M:%S')} ✅ 批量插入 {len(items)} 条: {items}")


def _flush_if_needed():
    """
    检查并刷新 - 你需要在每次添加数据后调用
    
    问题：忘了调用怎么办？
    """
    global _buffer, _last_flush_time
    
    if len(_buffer) >= BATCH_SIZE:
        batch = _buffer[:]
        _buffer = []
        _last_flush_time = time.time()
        
        try:
            batch_insert_to_db(batch)
        except Exception as e:
            # 失败了怎么办？数据丢了！
            print(f"❌ 失败了，丢了 {len(batch)} 条数据: {e}")


def _timeout_flush_thread():
    """
    后台超时刷新线程 - 你得自己写
    
    问题：
    1. daemon=True，主线程退出时数据可能丢失
    2. 不是 daemon，程序可能无法正常退出
    3. 忘了启动怎么办？
    """
    global _buffer, _last_flush_time, _running
    
    while _running:
        time.sleep(1)  # 轮询间隔，写死还是配置？
        
        with _lock:
            elapsed = time.time() - _last_flush_time
            if _buffer and elapsed >= BATCH_TIMEOUT:
                batch = _buffer[:]
                _buffer = []
                _last_flush_time = time.time()
                
                try:
                    batch_insert_to_db(batch)
                except Exception as e:
                    print(f"❌ 超时刷新失败: {e}")


def add_data(item):
    """
    添加数据 - 业务代码调用这个
    
    问题：
    1. 得记得加锁
    2. 得记得调用 flush
    3. 多个地方调用，容易漏
    """
    global _buffer
    
    with _lock:
        _buffer.append(item)
        _flush_if_needed()


def graceful_shutdown():
    """
    优雅退出 - 你得自己调用
    
    问题：忘了调用，最后一批数据就丢了
    """
    global _running, _buffer
    
    _running = False
    
    with _lock:
        if _buffer:
            print(f"关闭前刷新剩余 {len(_buffer)} 条...")
            batch = _buffer[:]
            _buffer = []
            batch_insert_to_db(batch)


# ============================================================
# 你还得在某个地方启动后台线程...
# ============================================================

def init_batch_system():
    """
    初始化 - 你得记得在程序启动时调用
    
    问题：忘了调用，超时刷新就不工作
    """
    t = threading.Thread(target=_timeout_flush_thread, daemon=True)
    t.start()
    print("后台线程已启动（记得调用 graceful_shutdown）")


# ============================================================
# 测试
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("临时手搞批量聚合 - 看看有多麻烦")
    print("=" * 60)
    
    # 你得记得初始化
    init_batch_system()
    
    # 模拟业务数据
    print("\n模拟产生 25 条数据...\n")
    for i in range(25):
        add_data({"id": i, "value": f"data_{i}"})
        print(f"  {time.strftime('%H:%M:%S')} 添加: id={i}")
        time.sleep(0.1)
    
    # 等待超时刷新
    print(f"\n等待 {BATCH_TIMEOUT}s 超时刷新剩余数据...\n")
    time.sleep(BATCH_TIMEOUT + 1)
    
    # 你得记得优雅退出
    graceful_shutdown()
    
    print("\n" + "=" * 60)
    print("总结：临时手搞的问题")
    print("=" * 60)
    print("""
1. 全局变量污染：_buffer, _lock, _last_flush_time, _running...
2. 容易忘记：
   - 忘了启动后台线程 → 超时刷新不工作
   - 忘了加锁 → 数据竞争
   - 忘了 graceful_shutdown → 最后一批数据丢失
3. 代码分散：初始化、添加、刷新、退出 散落在各处
4. 不可复用：下个项目又得重写一遍
5. 测试困难：全局状态难以 mock

而 funboost MicroBatchConsumerMixin：
   - 0 个全局变量
   - 2 个参数配置
   - 自动管理生命周期
   - 开箱即用
""")
