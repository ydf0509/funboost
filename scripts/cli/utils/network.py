# -*- coding: utf-8 -*-
"""
网络工具

检查网络连接、服务状态等
"""

import socket
import urllib.request
import urllib.error
from typing import Optional, Tuple, Dict, Any


class NetworkChecker:
    """网络检查工具类"""
    
    @classmethod
    def check_port(cls, host: str, port: int, timeout: float = 2.0) -> bool:
        """
        检查端口是否可连接
        
        Args:
            host: 主机地址
            port: 端口号
            timeout: 超时时间（秒）
        
        Returns:
            是否可连接
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    @classmethod
    def check_redis(
        cls,
        host: str = '127.0.0.1',
        port: int = 6379,
        password: str = None,
        db: int = 0
    ) -> Tuple[bool, str]:
        """
        检查 Redis 连接
        
        Returns:
            (是否连接成功, 状态信息)
        """
        try:
            import redis
            
            client = redis.Redis(
                host=host,
                port=port,
                password=password,
                db=db,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # 尝试 ping
            if client.ping():
                info = client.info('server')
                version = info.get('redis_version', 'unknown')
                return True, f"Redis {version}"
            
            return False, "Redis ping 失败"
            
        except ImportError:
            # 没有安装 redis 包，尝试直接 socket 连接
            if cls.check_port(host, port):
                return True, "Redis 端口可连接（未安装 redis 包，无法验证）"
            return False, "Redis 端口不可连接"
            
        except Exception as e:
            error_msg = str(e)
            if 'NOAUTH' in error_msg or 'AUTH' in error_msg:
                return False, "Redis 需要密码认证"
            elif 'Connection refused' in error_msg:
                return False, "Redis 连接被拒绝，服务可能未启动"
            return False, f"Redis 连接失败: {error_msg}"
    
    @classmethod
    def check_mongodb(
        cls,
        host: str = '127.0.0.1',
        port: int = 27017,
        username: str = None,
        password: str = None
    ) -> Tuple[bool, str]:
        """
        检查 MongoDB 连接
        
        Returns:
            (是否连接成功, 状态信息)
        """
        try:
            from pymongo import MongoClient
            from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
            
            # 构建连接 URI
            if username and password:
                uri = f"mongodb://{username}:{password}@{host}:{port}/"
            else:
                uri = f"mongodb://{host}:{port}/"
            
            client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            
            # 尝试获取服务器信息
            info = client.server_info()
            version = info.get('version', 'unknown')
            client.close()
            
            return True, f"MongoDB {version}"
            
        except ImportError:
            if cls.check_port(host, port):
                return True, "MongoDB 端口可连接（未安装 pymongo 包，无法验证）"
            return False, "MongoDB 端口不可连接"
            
        except Exception as e:
            error_msg = str(e)
            if 'Authentication failed' in error_msg:
                return False, "MongoDB 认证失败"
            elif 'Connection refused' in error_msg or 'ServerSelectionTimeoutError' in str(type(e)):
                return False, "MongoDB 连接被拒绝，服务可能未启动"
            return False, f"MongoDB 连接失败: {error_msg}"
    
    @classmethod
    def check_http_service(
        cls,
        url: str,
        timeout: float = 5.0,
        expected_status: int = None
    ) -> Tuple[bool, str]:
        """
        检查 HTTP 服务
        
        Args:
            url: 服务 URL
            timeout: 超时时间
            expected_status: 期望的状态码（None 表示任何 2xx/3xx）
        
        Returns:
            (是否正常, 状态信息)
        """
        try:
            request = urllib.request.Request(url, method='GET')
            request.add_header('User-Agent', 'CLI-Health-Check/1.0')
            
            response = urllib.request.urlopen(request, timeout=timeout)
            status = response.getcode()
            
            if expected_status:
                if status == expected_status:
                    return True, f"HTTP {status}"
                return False, f"HTTP {status}（期望 {expected_status}）"
            
            if 200 <= status < 400:
                return True, f"HTTP {status}"
            return False, f"HTTP {status}"
            
        except urllib.error.HTTPError as e:
            if expected_status and e.code == expected_status:
                return True, f"HTTP {e.code}"
            return False, f"HTTP {e.code}: {e.reason}"
            
        except urllib.error.URLError as e:
            reason = str(e.reason)
            if 'Connection refused' in reason:
                return False, "连接被拒绝，服务可能未启动"
            elif 'timed out' in reason.lower():
                return False, "连接超时"
            return False, f"连接失败: {reason}"
            
        except Exception as e:
            return False, f"检查失败: {str(e)}"
    
    @classmethod
    def check_backend_service(cls, port: int = 27018) -> Tuple[bool, str]:
        """检查后端服务"""
        return cls.check_http_service(f"http://127.0.0.1:{port}/")
    
    @classmethod
    def check_frontend_service(cls, port: int = 3000) -> Tuple[bool, str]:
        """检查前端服务"""
        return cls.check_http_service(f"http://127.0.0.1:{port}/")
    
    @classmethod
    def get_local_ip(cls) -> str:
        """获取本机 IP 地址"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(('8.8.8.8', 80))
            ip = sock.getsockname()[0]
            sock.close()
            return ip
        except Exception:
            return '127.0.0.1'
    
    @classmethod
    def check_internet(cls) -> bool:
        """检查是否有互联网连接"""
        try:
            socket.create_connection(('8.8.8.8', 53), timeout=3)
            return True
        except OSError:
            pass
        
        try:
            socket.create_connection(('1.1.1.1', 53), timeout=3)
            return True
        except OSError:
            pass
        
        return False
