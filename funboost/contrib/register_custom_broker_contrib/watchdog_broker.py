# -*- coding: utf-8 -*-

"""
# 一： 怎么使用
此文件演示 register_custom_broker 实现事件驱动型 broker。

Watchdog 文件系统监控 Broker - 事件驱动型消息队列

设计理念：
    - 无需手动发布消息，文件系统事件自动成为消息
    - 类似 MYSQL_CDC，是一种事件驱动的 broker
    - 适用场景：文件处理管道、日志监控、热更新、文件同步，文件变更事件驱动消费。

使用方式：（教程4b.11 有具体完整例子）

    
    @boost(BoosterParams(
        queue_name='file_processor',
        broker_kind=BrokerEnum.WATCHDOG,
        broker_exclusive_config={
            'watch_path': './data/inbox',
            'patterns': ['*.csv', '*.json'],
            'event_types': ['created'],
            'ack_action': 'delete',
        }
    ))
    def process_file(event_type, src_path, dest_path, is_directory, timestamp, file_content,): # 函数入参固定是这些就好了。
        print(f"收到文件: {src_path}")
        return f"处理完成"
    
    if __name__ == '__main__':
        process_file.consume()  # 向 ./data/inbox 放文件即可自动消费



# 二：为什么比原生 watchdog更好用
funboost 实现的watchdog broker 比直接使用原生watchdog更强大，因为funboost实现了原生watchdog不支持的功能

1. 自带 funboost 30多种复制控制功能，例如并发 qps 重试 等等
2. funboost 支持的 event_types 包含existing，原生watchdog不支持，funboost支持。
   完美解决funboost服务服务停止期间堆积的文件，或者处理历史已存在的文件，在原生watchdog中无法触发的问题。
3. 代码更简单，原生 watchdog 要写继承 EventHandler ，写 observer，funboost 只需要写一个消费者函数，就能自动处理所有文件事件。
4. 自带防抖功能，短时间内多次操作同一文件只触发一次消费。


# 三：变通妙用：
你可以将文件夹 作为消息队列，文件夹里面的每1个文件 taskidxx.json 作为一条消息。
这不就是相当于磁盘作为消息队列了吗？

"""

import os
import shutil
import threading
import time
from fnmatch import fnmatch
from pathlib import Path
from typing import Optional, List

try:
    from watchdog.observers import Observer
    from watchdog.events import PatternMatchingEventHandler
except ImportError:
    raise ImportError("请安装 watchdog: pip install watchdog")

from funboost import register_custom_broker, AbstractConsumer, AbstractPublisher, register_broker_exclusive_config_default
from funboost.core.helper_funs import get_task_id



# ============================================================================
# Publisher 实现
# ============================================================================

class WatchdogPublisher(AbstractPublisher):
    """
    Watchdog 发布者
    
    发布消息 = 在监控目录下创建文件
    这会触发 watchdog 的 created 事件，从而被消费者捕获
    """
    
    def custom_init(self):
        watch_path = self.publisher_params.broker_exclusive_config['watch_path']
        self._queue_dir = Path(watch_path)
        self._queue_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Watchdog Publisher 初始化完成，监控目录: {self._queue_dir.absolute().as_posix()}")

    def _publish_impl(self, msg: str):
        """
        watchdog 作为broker时候，不需要手动发布消息，但是任然支持。
        发消息也是funboost来写入文件，watchdog监听到文件变更后，自动触发消费者运行函数。
        """
        # raise NotImplementedError("Watchdog Broker 是事件驱动的，不支持手动 push 消息。请直接在监控目录下操作文件。")
        task_id = get_task_id(msg)
        file = self._queue_dir.joinpath(f'{task_id}.json')
        # 发布就是把消息写入文件，自动触发消费者运行函数。 
        file.write_text(msg)
        
    def clear(self):
        """清空监控目录下的所有消息文件"""
        # 注意：这可能会删除监控目录下的所有文件，需谨慎
        pass

    def get_message_count(self) -> int:
        """统计待处理文件数量"""
        if not self._queue_dir.exists():
            return 0
        # 简单统计文件数量，不递归
        return len([f for f in self._queue_dir.iterdir() if f.is_file()])

    def close(self):
        pass


# ============================================================================
# Consumer 实现
# ============================================================================

class FunboostEventHandler(PatternMatchingEventHandler):
    """
    Funboost 专用的文件事件处理器
    
    当文件事件发生时，将事件信息封装为消息并提交给消费者处理
    """
    
    def __init__(self, consumer: 'WatchdogConsumer', event_types: List[str], 
                 read_file_content: bool = False, debounce_seconds: Optional[float] = None, **kwargs):
        super().__init__(**kwargs)
        self._consumer = consumer
        self._event_types = set(event_types)
        self._read_file_content = read_file_content
        self._debounce_seconds = debounce_seconds
        # 防抖相关：存储每个文件路径对应的 Timer 和最新事件信息
        self._debounce_timers = {}  # {file_path: Timer}
        self._debounce_lock = threading.Lock()
    
    def _should_handle(self, event_type: str) -> bool:
        """检查是否应该处理此类型的事件"""
        return event_type in self._event_types
    
    def _handle_event(self, event, event_type: str):
        """统一的事件处理逻辑"""
        if not self._should_handle(event_type):
            return
        
        # 统一转换为绝对路径的 POSIX 格式（Linux 风格正斜杠）
        src_path = Path(event.src_path).absolute().as_posix()
        
        # dest_path 也统一转换
        dest_path = getattr(event, 'dest_path', None)
        if dest_path:
            dest_path = Path(dest_path).absolute().as_posix()
        
        # 构建消息体
        body = {
            'event_type': event_type,
            'src_path': src_path,
            'dest_path': dest_path,
            'is_directory': event.is_directory,
            'timestamp': time.time(),
            'file_content': None,
        }
        
        # 确定用于 ack 操作的文件路径：
        # - moved 事件：文件已移动到 dest_path，应使用 dest_path
        # - deleted 事件：文件已删除，file_path 仅作记录，ack 时会跳过
        # - 其他事件：使用 src_path
        if event_type == 'moved' and dest_path:
            file_path_for_ack = dest_path
        else:
            file_path_for_ack = src_path
        
        # 如果启用防抖，延迟提交任务
        if self._debounce_seconds is not None and self._debounce_seconds > 0:
            self._debounce_submit(file_path_for_ack, body, event_type)
        else:
            # 无防抖，直接提交
            self._do_submit(file_path_for_ack, body, event_type)
    
    def _do_submit(self, file_path: str, body: dict, event_type: str):
        """
        实际提交任务
        
        Args:
            file_path: 用于 ack 操作的文件路径（moved 事件时是 dest_path，其他事件是 src_path）
            body: 消息体
            event_type: 事件类型
        """
        # 可选：读取文件内容（仅小文件，且仅对文件仍存在的事件类型）
        # - created/modified/moved：文件存在，可以读取
        # - deleted：文件已删除，不读取
        if self._read_file_content and event_type in ('created', 'modified', 'moved'):
            try:
                if os.path.isfile(file_path) and os.path.getsize(file_path) < 1024 * 1024:  # < 1MB
                    body['file_content'] = Path(file_path).read_text(encoding='utf-8')
            except Exception:
                pass
        
        # 封装为 kw 字典并提交
        kw = {
            'body': body,
            'file_path': file_path,
        }
        self._consumer._submit_task(kw)
        self._consumer.logger.debug(f"捕获文件事件: {event_type} - {file_path}")
    
    def _debounce_submit(self, file_path: str, body: dict, event_type: str):
        """
        防抖提交：在指定时间内如果有新事件，取消旧的定时器，重新计时
        
        Args:
            file_path: 用于 ack 操作的文件路径（也用作防抖 key）
            body: 消息体
            event_type: 事件类型
        """
        with self._debounce_lock:
            # 取消该文件路径已有的定时器
            if file_path in self._debounce_timers:
                old_timer = self._debounce_timers[file_path]
                old_timer.cancel()
                self._consumer.logger.debug(f"防抖: 取消旧定时器 - {file_path}")
            
            # 创建新的定时器，延迟执行提交
            def delayed_submit():
                with self._debounce_lock:
                    self._debounce_timers.pop(file_path, None)
                self._do_submit(file_path, body, event_type)
                self._consumer.logger.debug(f"防抖: 定时器触发提交 - {file_path}")
            
            timer = threading.Timer(self._debounce_seconds, delayed_submit)
            self._debounce_timers[file_path] = timer
            timer.start()
            self._consumer.logger.debug(f"防抖: 设置新定时器 {self._debounce_seconds}s - {file_path}")
    
    def on_created(self, event):
        self._handle_event(event, 'created')
    
    def on_modified(self, event):
        self._handle_event(event, 'modified')
    
    def on_deleted(self, event):
        self._handle_event(event, 'deleted')
    
    def on_moved(self, event):
        self._handle_event(event, 'moved')


class WatchdogConsumer(AbstractConsumer):
    """
    Watchdog 消费者
    
    监听文件系统事件，将事件作为消息自动消费
    这是一种事件驱动型 broker，无需用户手动发布消息
    """
    
    BROKER_KIND = None  # 会被框架自动设置

    def custom_init(self):
        # 从 broker_exclusive_config 获取配置
        config = self.consumer_params.broker_exclusive_config
        
        # 用户必须要在装饰器的 broker_exclusive_config 中配置以下字段，否则会报错。
        watch_path = config['watch_path']  
        self._patterns = config['patterns']
        self._ignore_patterns = config['ignore_patterns']
        self._ignore_directories = config['ignore_directories']
        self._case_sensitive = config['case_sensitive']
        self._event_types = config['event_types']
        self._recursive = config['recursive']
        # ack_action: 'delete' | 'archive' | 'none'
        self._ack_action = config['ack_action']
        self._read_file_content = config['read_file_content']
        # 防抖时间（秒），None 或 0 表示不防抖
        self._debounce_seconds = config['debounce_seconds']
        
        # 确定监控目录：直接使用 watch_path，queue_name 仅作标识
        self._queue_dir = Path(watch_path).absolute()
        self._queue_dir.mkdir(parents=True, exist_ok=True)
        
        # 归档目录配置（仅 archive 模式需要）
        self._archive_dir = None
        if self._ack_action == 'archive':
            archive_path = config['archive_path']
            if not archive_path:
                raise ValueError("ack_action='archive' 时必须配置 archive_path 归档目录")
            
            self._archive_dir = Path(archive_path).absolute()
            
            # 验证：归档目录不能是监控目录的子目录（否则会触发重复事件）
            if self._is_subpath(self._archive_dir, self._queue_dir):
                raise ValueError(
                    f"archive_path 不能是 watch_path 的子目录！\n"
                    f"  watch_path: {self._queue_dir.as_posix()}\n"
                    f"  archive_path: {self._archive_dir.as_posix()}\n"
                    f"请将 archive_path 设置为监控目录外部的路径。"
                )
            
            self._archive_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"归档目录: {self._archive_dir.as_posix()}")
        
        self._observer = None
        
        self.logger.info(
            f"Watchdog Consumer 初始化完成，监控目录: {self._queue_dir.as_posix()}, "
            f"事件类型: {self._event_types}, 文件模式: {self._patterns}"
        )

    def _dispatch_task(self):
        """
        核心调度方法
        启动 watchdog Observer 监听文件系统事件
        """
        # 先处理目录中已存在的文件
        self._process_existing_files()
        
        # 创建事件处理器
        event_handler = FunboostEventHandler(
            consumer=self,
            event_types=self._event_types,
            read_file_content=self._read_file_content,
            debounce_seconds=self._debounce_seconds,
            patterns=self._patterns,
            ignore_patterns=self._ignore_patterns,
            ignore_directories=self._ignore_directories,
            case_sensitive=self._case_sensitive,
        )
        
        # 创建并启动 Observer
        self._observer = Observer()
        self._observer.schedule(event_handler, self._queue_dir.as_posix(), recursive=self._recursive)
        self._observer.start()
        
        self.logger.info(f"Watchdog Observer 已启动，正在监听: {self._queue_dir.as_posix()}")
        
        # 保持运行，不退出 ，因为_dispatch_task是会被父类死循环调用
        while True:
            time.sleep(100)
      
    
    def _process_existing_files(self):
        """处理启动时已存在的待处理文件"""
        # 如果 event_types 不包含 'existing'，跳过处理已存在的文件
        if 'existing' not in self._event_types:
            return
        
        if not self._queue_dir.exists():
            return
        
        if self._recursive:
            all_items = list(self._queue_dir.rglob('*'))
        else:
            all_items = list(self._queue_dir.glob('*'))
        
        # 过滤：只保留文件，且匹配文件模式
        existing_files = []
        for file_path in all_items:
            # 排除目录
            if not file_path.is_file():
                continue
            # 检查是否匹配模式（使用完整路径，与 PatternMatchingEventHandler 行为一致）
            if not self._match_patterns(file_path.absolute().as_posix()):
                continue
            existing_files.append(file_path)
            
        if existing_files:
            self.logger.info(f"发现 {len(existing_files)} 个待处理文件")
        
        for file_path in existing_files:
            body = {
                'event_type': 'existing',
                'src_path': file_path.absolute().as_posix(),
                'dest_path': None,
                'is_directory': False,
                'timestamp': time.time(),
                'file_content': None,
            }
            
            if self._read_file_content:
                try:
                    if file_path.stat().st_size < 1024 * 1024:
                        body['file_content'] = file_path.read_text(encoding='utf-8')
                except Exception:
                    pass
            
            kw = {
                'body': body,
                'file_path': file_path.absolute().as_posix(),
            }
            self._submit_task(kw)
    
    @staticmethod
    def _is_subpath(child: Path, parent: Path) -> bool:
        """检查 child 是否是 parent 的子目录"""
        try:
            child.relative_to(parent)
            return True
        except ValueError:
            return False

    def _match_patterns(self, file_path: str) -> bool:
        """
        检查文件路径是否匹配模式（与 PatternMatchingEventHandler 行为一致）
        
        Args:
            file_path: 文件的完整路径（POSIX 格式）
        """
        # 如果不区分大小写，统一转为小写比较
        if not self._case_sensitive:
            path_cmp = file_path.lower()
            patterns = [p.lower() for p in self._patterns]
            ignore_patterns = [p.lower() for p in self._ignore_patterns]
        else:
            path_cmp = file_path
            patterns = self._patterns
            ignore_patterns = self._ignore_patterns
        
        # 先检查是否匹配忽略模式
        for pattern in ignore_patterns:
            if fnmatch(path_cmp, pattern):
                return False
        
        # 再检查是否匹配包含模式
        if patterns == ['*']:
            return True
        for pattern in patterns:
            if fnmatch(path_cmp, pattern):
                return True
        return False

    def _confirm_consume(self, kw):
        """
        确认消费成功
        根据配置决定删除文件还是移动到归档目录
        """
        file_path = kw.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return
        
        try:
            if self._ack_action == 'delete':
                os.unlink(file_path)
                self.logger.debug(f"消费确认，已删除文件: {file_path}")
            elif self._ack_action == 'archive':
                # 移动到归档目录，保持相对路径结构
                file_path_obj = Path(file_path)
                # 计算文件相对于监控目录的相对路径
                relative_path = file_path_obj.relative_to(self._queue_dir)
                # 在归档目录中保持相同的相对路径
                dest = self._archive_dir / relative_path
                # 确保目标目录存在
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(file_path, dest.as_posix())
                self.logger.debug(f"消费确认，已归档文件到: {dest.as_posix()}")
            else:
                # ack_action == 'none'，纯监控模式
                self.logger.debug(f"消费确认，纯监控模式，文件保持原位: {file_path}")
        except Exception as e:
            self.logger.warning(f"确认消费时处理文件失败: {e}")

    def _requeue(self, kw):
        """
        消息重入队（仅 archive 模式有效）
        将归档目录中的文件移回监控目录，触发重新消费
        """
        if self._ack_action != 'archive' or not self._archive_dir:
            self.logger.warning("requeue 仅在 ack_action='archive' 模式下有效")
            return
        
        file_path = kw.get('file_path')
        if not file_path:
            return
        
        # 计算文件相对于监控目录的相对路径
        file_path_obj = Path(file_path)
        try:
            relative_path = file_path_obj.relative_to(self._queue_dir)
        except ValueError:
            # 如果无法计算相对路径，使用文件名
            relative_path = file_path_obj.name
        
        # 检查归档目录中对应位置的文件
        archived_path = self._archive_dir / relative_path
        if archived_path.exists():
            try:
                # 移回监控目录，保持相对路径结构
                dest = self._queue_dir / relative_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(archived_path.as_posix(), dest.as_posix())
                self.logger.info(f"消息重入队，已移动文件回: {dest.as_posix()}")
            except Exception as e:
                self.logger.warning(f"重入队时移动文件失败: {e}")


# ============================================================================
# 注册 Broker
# ============================================================================

BROKER_KIND_WATCHDOG = 'WATCHDOG'


register_broker_exclusive_config_default(
    BROKER_KIND_WATCHDOG,
    {
        'watch_path': './watchdog_queues',      # 监控根目录
        'patterns': ['*'],                       # 匹配的文件模式
        'ignore_patterns': [],                   # 忽略的文件模式
        'ignore_directories': True,              # 是否忽略目录事件
        'case_sensitive': False,                 # 是否区分大小写
        
         # event_types 枚举大全: ['created', 'modified', 'deleted', 'moved', 'existing']
         # created: 文件新建; modified: 文件修改; deleted: 文件删除; moved: 文件移动; 
         # existing: 启动时已存在的文件是否触发funboost消费,原生的watchdog不支持，funboost支持，完美解决funboost服务重启后，停机期间堆积的文件
        'event_types': ['created', 'modified'],  
        # 监听的事件类型，如果是一次性写入文件，只监听modified就好，不然每次写入一个新的文件会触发created 和 modified总计2次。
        
        'recursive': False,                      # 是否递归监控子目录
        
        # ack_action 枚举: 'delete' | 'archive' | 'none'
        # delete: 消费后删除文件; archive: 消费后归档到 archive_path; none: 纯监控模式，什么都不做
        'ack_action': 'delete',              # 消费后操作
        
        # 归档目录路径（仅 ack_action='archive' 时需要）
        # 重要：archive_path 不能是 watch_path 的子目录，否则会触发重复事件！
        'archive_path': None,
        
        'read_file_content': True,               # 是否读取文件内容（小于1MB的文件）
        
        # 防抖时间（秒）：None 表示不防抖，设置数值则在该时间内对同一文件的多次事件只触发一次消费
        # 例如：debounce_seconds=2，则第0秒创建文件、第1秒修改、第2秒又修改，只会在最后一次修改后2秒触发一次消费
        'debounce_seconds': 0.5,
    }
)

register_custom_broker(BROKER_KIND_WATCHDOG, WatchdogPublisher, WatchdogConsumer)


# ============================================================================
# 测试代码
# ============================================================================


