# -*- coding: utf-8 -*-
"""
使用 watchdog 实现 Flask 自动重启

优点：
1. 不依赖 Flask 自带的 debug 重启，更稳定
2. 只监控指定目录，避免无关文件变化触发重启
3. 即使代码有语法错误，监控进程也不会崩溃
4. 可配置延迟重启，防止保存一半就重启
"""

import subprocess
import sys
import time
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


class FlaskReloader:
    """Flask 自动重启器"""
    
    def __init__(self, flask_script: str, watch_dirs: list = None, 
                 watch_files: list = None, patterns: list = None, delay: float = 1.0):
        """
        Args:
            flask_script: Flask 启动脚本路径
            watch_dirs: 要监控的目录列表（目录下所有文件）
            watch_files: 要监控的单个文件列表（精确匹配）
            patterns: 要监控的文件模式，默认 ['*.py']
            delay: 检测到变化后延迟多少秒再重启，默认 1 秒
        """
        self.flask_script = flask_script
        self.watch_dirs = [Path(d) for d in (watch_dirs or [])]
        # 单个文件列表，存储规范化的绝对路径
        self.watch_files = [Path(f).resolve() for f in (watch_files or [])]
        self.patterns = patterns or ['*.py']
        self.delay = delay
        self.process = None
        self.observer = None
        self._last_change_time = 0
        self._pending_restart = False
    
    def start_flask(self):
        """启动 Flask 进程"""
        if self.process:
            self.stop_flask()
        
        print(f"\n{'='*60}")
        print(f"[FlaskReloader] 启动 Flask: {self.flask_script}")
        print(f"{'='*60}\n")
        
        # 使用当前 Python 解释器启动 Flask
        self.process = subprocess.Popen(
            [sys.executable, self.flask_script],
            cwd=os.path.dirname(self.flask_script) or '.',
        )
    
    def stop_flask(self):
        """停止 Flask 进程"""
        if self.process:
            print(f"\n[FlaskReloader] 停止 Flask (PID: {self.process.pid})")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
    
    def restart_flask(self):
        """重启 Flask"""
        print(f"\n[FlaskReloader] 检测到文件变化，{self.delay} 秒后重启...")
        time.sleep(self.delay)
        self.start_flask()
        self._pending_restart = False
    
    def on_file_changed(self, event):
        """文件变化回调"""
        # 忽略目录事件
        if event.is_directory:
            return
        
        src_path = Path(event.src_path).resolve()
        
        # 如果指定了单个文件列表，检查是否在列表中
        if self.watch_files:
            # 检查是否精确匹配单个文件
            if src_path not in self.watch_files:
                # 不在单文件列表中，检查是否在监控目录下
                in_watch_dir = False
                for d in self.watch_dirs:
                    try:
                        src_path.relative_to(d.resolve())
                        in_watch_dir = True
                        break
                    except ValueError:
                        continue
                if not in_watch_dir:
                    return  # 不在监控范围内，忽略
        
        # 防抖：短时间内多次变化只触发一次重启
        now = time.time()
        if now - self._last_change_time < 0.5:
            return
        self._last_change_time = now
        
        print(f"[FlaskReloader] 文件变化: {src_path}")
        
        # 标记需要重启，在主循环中处理
        self._pending_restart = True
    
    def run(self):
        """运行重载器"""
        # 创建事件处理器
        handler = PatternMatchingEventHandler(
            patterns=self.patterns,
            ignore_patterns=['*/__pycache__/*', '*.pyc'],
            ignore_directories=True,
            case_sensitive=False,
        )
        handler.on_modified = self.on_file_changed
        handler.on_created = self.on_file_changed
        
        # 创建观察者并添加监控目录
        self.observer = Observer()
        
        # 收集所有需要监控的目录（包括单文件的父目录）
        all_watch_dirs = set(self.watch_dirs)
        for f in self.watch_files:
            all_watch_dirs.add(f.parent)
        
        for watch_dir in all_watch_dirs:
            if watch_dir.exists():
                self.observer.schedule(handler, str(watch_dir), recursive=True)
                print(f"[FlaskReloader] 监控目录: {watch_dir}")
            else:
                print(f"[FlaskReloader] 警告: 目录不存在 {watch_dir}")
        
        # 启动观察者和 Flask
        self.observer.start()
        self.start_flask()
        
        print("\n[FlaskReloader] 自动重载已启动，按 Ctrl+C 停止\n")
        
        try:
            while True:
                # 检查是否需要重启
                if self._pending_restart:
                    self.restart_flask()
                
                # 检查 Flask 进程是否意外退出
                if self.process and self.process.poll() is not None:
                    print(f"\n[FlaskReloader] Flask 进程退出 (code: {self.process.returncode})")
                    print("[FlaskReloader] 等待文件变化后自动重启...")
                    self.process = None
                    # 等待下一次文件变化触发重启
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n[FlaskReloader] 收到中断信号，正在停止...")
        finally:
            self.stop_flask()
            self.observer.stop()
            self.observer.join()
            print("[FlaskReloader] 已停止")


if __name__ == '__main__':
    # 项目根目录
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    
    # Flask 启动脚本
    FLASK_SCRIPT = str(PROJECT_ROOT / 'funboost' / 'funboost_web_manager' / 'app_debug_start.py')
    
    # 要监控的目录（目录下所有 .py 文件变化都会触发重启）
    WATCH_DIRS = [
        PROJECT_ROOT / 'funboost' / 'faas',
        PROJECT_ROOT / 'funboost' / 'funboost_web_manager',
    ]
    
    # 要监控的单个文件（精确匹配，只有这些文件变化才会触发重启）
    WATCH_FILES = [
        PROJECT_ROOT / 'funboost' / 'core' / 'active_cousumer_info_getter.py',
    ]
    
    # 单文件需要监控其父目录，但只在回调中过滤
    watch_dirs_for_observer = list(WATCH_DIRS)
    for f in WATCH_FILES:
        if f.parent not in watch_dirs_for_observer:
            watch_dirs_for_observer.append(f.parent)
    
    print("=" * 60)
    print("Flask watchdog 自动重载器")
    print("=" * 60)
    print(f"Flask 脚本: {FLASK_SCRIPT}")
    print("监控目录:")
    for d in WATCH_DIRS:
        print(f"  - {d}")
    print("监控单文件:")
    for f in WATCH_FILES:
        print(f"  - {f}")
    print("=" * 60)
    
    reloader = FlaskReloader(
        flask_script=FLASK_SCRIPT,
        watch_dirs=WATCH_DIRS,
        watch_files=WATCH_FILES,
        patterns=['*.py'],
        delay=5.0,  # 检测到变化后等待 5 秒再重启。
    )
    reloader.run()
