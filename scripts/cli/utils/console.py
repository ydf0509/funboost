# -*- coding: utf-8 -*-
"""
控制台输出工具

提供彩色输出、进度条、表格等功能
"""

import sys
import os
from typing import Optional, List, Dict, Any


class Colors:
    """ANSI 颜色代码"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # 前景色
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # 亮色
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'


class Console:
    """控制台输出工具"""
    
    # 是否启用颜色
    _color_enabled: bool = True
    
    @classmethod
    def _supports_color(cls) -> bool:
        """检查终端是否支持颜色"""
        # Windows 需要特殊处理
        if sys.platform == 'win32':
            # Windows 10+ 支持 ANSI
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except Exception:
                return os.environ.get('TERM') is not None
        
        # Unix 系统检查 TERM
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    
    @classmethod
    def disable_color(cls):
        """禁用颜色输出"""
        cls._color_enabled = False
    
    @classmethod
    def enable_color(cls):
        """启用颜色输出"""
        cls._color_enabled = True
    
    @classmethod
    def _colorize(cls, text: str, color: str) -> str:
        """添加颜色"""
        if not cls._color_enabled or not cls._supports_color():
            return text
        return f"{color}{text}{Colors.RESET}"
    
    @classmethod
    def success(cls, message: str, prefix: str = "✓"):
        """成功消息（绿色）"""
        print(cls._colorize(f"{prefix} {message}", Colors.GREEN))
    
    @classmethod
    def error(cls, message: str, prefix: str = "✗"):
        """错误消息（红色）"""
        print(cls._colorize(f"{prefix} {message}", Colors.RED))
    
    @classmethod
    def warning(cls, message: str, prefix: str = "⚠"):
        """警告消息（黄色）"""
        print(cls._colorize(f"{prefix} {message}", Colors.YELLOW))
    
    @classmethod
    def info(cls, message: str, prefix: str = "ℹ"):
        """信息消息（蓝色）"""
        print(cls._colorize(f"{prefix} {message}", Colors.BLUE))
    
    @classmethod
    def dim(cls, message: str):
        """暗淡文本"""
        print(cls._colorize(message, Colors.DIM))
    
    @classmethod
    def bold(cls, message: str):
        """粗体文本"""
        print(cls._colorize(message, Colors.BOLD))
    
    @classmethod
    def title(cls, message: str):
        """标题（青色粗体）"""
        print()
        print(cls._colorize(f"{'=' * 60}", Colors.CYAN))
        print(cls._colorize(f"  {message}", Colors.BOLD + Colors.CYAN))
        print(cls._colorize(f"{'=' * 60}", Colors.CYAN))
    
    @classmethod
    def subtitle(cls, message: str):
        """副标题"""
        print()
        print(cls._colorize(f"[{message}]", Colors.BOLD))
        print(cls._colorize("-" * 40, Colors.DIM))
    
    @classmethod
    def step(cls, current: int, total: int, message: str):
        """步骤提示"""
        print()
        print(cls._colorize(f"[{current}/{total}] {message}", Colors.CYAN))
    
    @classmethod
    def item(cls, message: str, indent: int = 2, last: bool = False):
        """列表项"""
        prefix = "└─" if last else "├─"
        print(f"{' ' * indent}{prefix} {message}")
    
    @classmethod
    def newline(cls):
        """空行"""
        print()
    
    @classmethod
    def hint(cls, message: str):
        """提示信息"""
        print()
        print(cls._colorize(f"提示: {message}", Colors.DIM))
    
    @classmethod
    def suggestion(cls, title: str, items: List[str]):
        """解决建议"""
        print()
        print(cls._colorize(f"  {title}:", Colors.YELLOW))
        for item in items:
            print(cls._colorize(f"  - {item}", Colors.DIM))
    
    @classmethod
    def confirm(cls, message: str, default: bool = False) -> bool:
        """确认提示"""
        suffix = "[Y/n]" if default else "[y/N]"
        try:
            response = input(f"{message} {suffix}: ").strip().lower()
            if not response:
                return default
            return response in ('y', 'yes', '是')
        except (KeyboardInterrupt, EOFError):
            print()
            return False
    
    @classmethod
    def select(cls, message: str, options: List[str], default: int = 0) -> int:
        """选择菜单"""
        print(f"\n{message}")
        for i, option in enumerate(options):
            marker = ">" if i == default else " "
            print(f"  {marker} [{i + 1}] {option}")
        
        try:
            response = input(f"\n请选择 [1-{len(options)}] (默认: {default + 1}): ").strip()
            if not response:
                return default
            choice = int(response) - 1
            if 0 <= choice < len(options):
                return choice
            return default
        except (ValueError, KeyboardInterrupt, EOFError):
            return default
    
    @classmethod
    def input(cls, message: str, default: str = "") -> str:
        """输入提示"""
        suffix = f" [{default}]" if default else ""
        try:
            response = input(f"{message}{suffix}: ").strip()
            return response if response else default
        except (KeyboardInterrupt, EOFError):
            print()
            return default
    
    @classmethod
    def password(cls, message: str) -> str:
        """密码输入（不回显）"""
        import getpass
        try:
            return getpass.getpass(f"{message}: ")
        except (KeyboardInterrupt, EOFError):
            print()
            return ""
    
    @classmethod
    def table(cls, headers: List[str], rows: List[List[str]], title: str = None):
        """简单表格"""
        if title:
            print(f"\n{title}")
        
        # 计算列宽
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(str(cell)))
        
        # 打印表头
        header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
        print(f"\n  {header_line}")
        print(f"  {'-' * len(header_line)}")
        
        # 打印数据行
        for row in rows:
            row_line = " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
            print(f"  {row_line}")
    
    @classmethod
    def progress(cls, current: int, total: int, width: int = 40, prefix: str = ""):
        """进度条"""
        percent = current / total if total > 0 else 0
        filled = int(width * percent)
        bar = "█" * filled + "░" * (width - filled)
        percent_str = f"{percent * 100:.0f}%"
        
        # 使用 \r 覆盖当前行
        sys.stdout.write(f"\r{prefix} [{bar}] {percent_str}")
        sys.stdout.flush()
        
        if current >= total:
            print()  # 完成后换行
    
    @classmethod
    def clear_line(cls):
        """清除当前行"""
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()
