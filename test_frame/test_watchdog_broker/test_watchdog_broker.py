# -*- coding: utf-8 -*-
"""
测试 Watchdog 文件系统监控 Broker

Watchdog Broker 是事件驱动型中间件：
1. 无需手动发布消息
2. 文件创建/修改自动触发消费
3. 适合文件处理管道场景
4. 证明 funboost 中万物可为broker，funboost具有超高无限的扩展性
"""

import time
from pathlib import Path


from funboost import boost, BoosterParams, ctrl_c_recv, BrokerEnum


# 测试目录
TEST_DIR = Path(__file__).parent / "watchdog_test_data"
# 归档目录（必须在监控目录外部）
ARCHIVE_DIR = Path(__file__).parent / "watchdog_archive"


@boost(
    BoosterParams(
        queue_name="test_file_processor",
        broker_kind=BrokerEnum.WATCHDOG,
        qps=10,
        concurrent_num=3,
        broker_exclusive_config={
            # ==================== 必填配置 ====================
            "watch_path": TEST_DIR.absolute().as_posix(),  # 监控目录路径（必须使用绝对路径的 POSIX 格式）
            
            # ==================== 文件匹配配置 ====================
            "patterns": ["*.txt", "*.json", "*.csv", "*.msg"],  # 匹配的文件模式，['*'] 表示所有文件
            "ignore_patterns": [],               # 忽略的文件模式，如 ['*.tmp', '*.log']
            "ignore_directories": True,          # 是否忽略目录事件
            "case_sensitive": False,             # 文件名匹配是否区分大小写
            
            # ==================== 事件类型配置 ====================
            # event_types 枚举: ['created', 'modified', 'deleted', 'moved', 'existing']
            # - created: 文件新建
            # - modified: 文件修改
            # - deleted: 文件删除
            # - moved: 文件移动/重命名
            # - existing: 启动时已存在的文件（原生 watchdog 不支持，funboost 扩展支持）
            "event_types": [
                "created",   # 如果只监听 modified，则一次性写入文件只触发1次；同时监听 created+modified 会触发2次
                "existing",    # 完美解决 funboost 服务重启后，停机期间堆积的文件
                "modified",
            ],
            
            # ==================== 目录递归配置 ====================
            "recursive": True,                  # 是否递归监控子目录
            
            # ==================== 消费确认配置 ====================
            # ack_action 枚举: 'delete' | 'archive' | 'none'
            # - delete: 消费成功后删除文件
            # - archive: 消费成功后移动到 archive_path 指定的目录
            # - none: 纯监控模式，不做任何操作
            "ack_action": "archive",
            
            # ==================== 归档目录配置 ====================
            # 仅 ack_action='archive' 时需要配置
            # 重要：archive_path 不能是 watch_path 的子目录！
            "archive_path": ARCHIVE_DIR.absolute().as_posix(),
            
            # ==================== 文件内容读取 ====================
            "read_file_content": True,           # 是否自动读取文件内容（仅小于 1MB 的文件）
            
            # ==================== 防抖配置 ====================
            # debounce_seconds: None | float
            # - None: 不防抖，每次文件事件都触发消费
            # - float: 防抖时间（秒），在该时间内对同一文件的多次事件只触发一次消费
            # 例如：debounce_seconds=2，第0秒创建文件、第1秒修改、第2秒又修改，只会在最后一次修改后2秒触发一次消费
            "debounce_seconds": 30,               # 2秒防抖，短时间内多次操作同一文件只触发一次
        },
        should_check_publish_func_params=False,
    )
)
def process_file(   # 此函数入参固定是这些就可以了。
    event_type,
    src_path,
    dest_path,
    is_directory,
    timestamp,
    file_content,
):
    print(locals())
    """处理文件事件"""
    print(f"[{event_type}] 处理文件: {src_path}")
    if file_content:
        preview = (
            file_content[:500] + "..." if len(file_content) > 500 else file_content
        )
        print(f"  内容预览: {preview}")
    time.sleep(0.3)
    return f"处理完成: {Path(src_path).name}"


def create_test_files():
    """创建测试文件，触发文件创建和文件修改事件"""
    pending_dir = TEST_DIR
    pending_dir.mkdir(parents=True, exist_ok=True)

    print(f"创建测试文件到: {pending_dir}")

    for i in range(5):
        file_path = pending_dir / f"test_file_{i}.txt"
        file_path.write_text(f"这是测试文件 {i}\n内容行 1\n内容行 2", encoding="utf-8")
        print(f"  创建: {file_path.name}")

    print(f"已创建 5 个测试文件")


def manual_push():
    """
    watchdog作为broker时候， funboost 允许手动发布消息，
    但手动发布消息是非必须的，原理是watchdog监听到文件变更后，自动触发消费者运行函数，所以不需要人工调用push方法。
    """
    for i in range(3):
        process_file.push(a=i, b=i * 2)


if __name__ == "__main__":
    process_file.consume()
    time.sleep(5)
    create_test_files()
    manual_push()
    ctrl_c_recv()
