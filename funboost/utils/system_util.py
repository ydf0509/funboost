
import os
import sys
import platform
import socket
import threading
import uuid
import multiprocessing
import inspect

def is_windows():
    return os.name == 'nt'

def is_linux():
    return os.name == 'posix' and platform.system() == 'Linux'

def is_mac():
    return platform.system() == 'Darwin'

def get_os_str():
    return platform.system()

def get_hostname():
    return socket.gethostname()

def get_host_ip():
    """获取本机ip"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return '127.0.0.1'

def get_mac_address():
    """获取mac地址"""
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e + 2] for e in range(0, 11, 2)])

def get_pid():
    return os.getpid()

def get_thread_id():
    return threading.get_ident()

def get_process_name():
    return multiprocessing.current_process().name

def get_current_thread_name():
    return threading.current_thread().name

def get_cpu_count():
    try:
        return multiprocessing.cpu_count()
    except Exception:
        return 1

def get_python_version():
    return platform.python_version()

def get_current_function_name():
    """获取当前函数名"""
    return inspect.stack()[1][3]