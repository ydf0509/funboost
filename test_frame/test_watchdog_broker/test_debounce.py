# -*- coding: utf-8 -*-
"""
测试 Watchdog Broker 的防抖功能

防抖功能说明：
- debounce_seconds=None: 不防抖，每次文件事件都触发消费
- debounce_seconds=2: 2秒防抖，在2秒内对同一文件的多次事件只触发一次消费

测试场景：
1. 第0秒创建文件
2. 第0.5秒修改文件
3. 第1秒再次修改文件
如果设置 debounce_seconds=2，以上操作只会触发1次消费（在最后一次修改后2秒触发）
"""

import time
from pathlib import Path
from funboost import boost, BoosterParams, ctrl_c_recv, BrokerEnum

# 测试目录
TEST_DIR = Path(__file__).parent / "debounce_test_data"

# 记录触发次数
trigger_count = 0


@boost(
    BoosterParams(
        queue_name="test_debounce_processor",
        broker_kind=BrokerEnum.WATCHDOG,
        qps=10,
        concurrent_num=3,
        broker_exclusive_config={
            "watch_path": TEST_DIR.absolute().as_posix(),
            "patterns": ["*.txt"],
            "ignore_patterns": [],
            "ignore_directories": True,
            "case_sensitive": False,
            "event_types": ["created", "modified"],  # 同时监听创建和修改
            "recursive": False,
            "ack_action": "none",  # 纯监控模式，不删除文件，方便观察
            "read_file_content": True,
            # ==================== 防抖配置 ====================
            # 设置为 2 秒防抖
            # 如果设置为 None，则每次文件事件都触发消费
            "debounce_seconds": 2,
        },
        should_check_publish_func_params=False,
    )
)
def process_file_debounce(
    event_type,
    src_path,
    dest_path,
    is_directory,
    timestamp,
    file_content,
):
    """处理文件事件（带防抖）"""
    global trigger_count
    trigger_count += 1
    print(f"\n{'='*60}")
    print(f"[触发次数: {trigger_count}] [{event_type}] 文件: {Path(src_path).name}")
    print(f"  时间戳: {time.strftime('%H:%M:%S', time.localtime(timestamp))}")
    if file_content:
        print(f"  内容: {file_content[:100]}")
    print(f"{'='*60}\n")
    return f"处理完成: {Path(src_path).name}"


def test_debounce():
    """
    测试防抖效果
    
    对同一个文件进行多次快速操作，观察是否只触发一次消费
    """
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("开始测试防抖功能 (debounce_seconds=2)")
    print("="*60)
    
    test_file = TEST_DIR / "debounce_test.txt"
    
    # 第0秒：创建文件
    print(f"\n[{time.strftime('%H:%M:%S')}] 创建文件...")
    test_file.write_text("版本1: 初始内容", encoding="utf-8")
    
    # 第0.5秒：修改文件
    time.sleep(0.5)
    print(f"[{time.strftime('%H:%M:%S')}] 第1次修改...")
    test_file.write_text("版本2: 第一次修改", encoding="utf-8")
    
    # 第1秒：再次修改
    time.sleep(0.5)
    print(f"[{time.strftime('%H:%M:%S')}] 第2次修改...")
    test_file.write_text("版本3: 第二次修改", encoding="utf-8")
    
    # 第1.5秒：第三次修改
    time.sleep(0.5)
    print(f"[{time.strftime('%H:%M:%S')}] 第3次修改...")
    test_file.write_text("版本4: 第三次修改", encoding="utf-8")
    
    print(f"\n[{time.strftime('%H:%M:%S')}] 完成4次文件操作（1次创建 + 3次修改）")
    print("如果防抖生效，应该只触发1次消费（在最后一次修改后2秒）")
    print(f"预计触发时间: {time.strftime('%H:%M:%S', time.localtime(time.time() + 2))}")
    print("等待防抖定时器触发...\n")


if __name__ == "__main__":
    process_file_debounce.consume()
    time.sleep(3)  # 等待消费者启动
    test_debounce()
    print("\n等待观察结果（约10秒后可 Ctrl+C 退出）...\n")
    ctrl_c_recv()
