
"""
python3.7 没有uuid7，自己实现。

uuid7比uuid4对数据库更友好，类似雪花算法

UUIDv4 完全无法知道生成时间；
UUIDv7 可以精确还原生成时间（毫秒级）。
"""

import time
import secrets
import uuid
from datetime import datetime
import random

def uuid7() -> uuid.UUID:
    """
    RFC 9562 UUIDv7
    """
    # 1. 毫秒时间戳（48 bits）
    ts_ms = int(time.time() * 1000) & ((1 << 48) - 1)

    # 2. 填充剩余的 80 bits 为随机数
    # 注意：我们先填满低 80 位，后面再通过位运算覆盖 Version 和 Variant
    rand_payload = secrets.randbits(80)

    # 3. 拼接时间戳到高位
    value = (ts_ms << 80) | rand_payload

    # 4. 设置 Version 7 (0111)
    # 位置：bits 76-79 (从右往左数，0-indexed)
    value &= ~(0xF << 76)  # 清除这 4 位
    value |= (0x7 << 76)   # 写入 0111

    # 5. 设置 Variant (10xx) - 这是原代码缺失的关键部分
    # 位置：bits 62-63
    # RFC 9562 要求 Variant 为 2 (即二进制 10)
    value &= ~(0x3 << 62)  # 清除这 2 位
    value |= (0x2 << 62)   # 写入 10

    return uuid.UUID(int=value)



def uuid7_fast() -> uuid.UUID:
    ts_ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand_payload = random.getrandbits(80)  # 比 secrets 快 5-10 倍
    value = (ts_ms << 80) | rand_payload
    value &= ~(0xF << 76)
    value |= (0x7 << 76)
    value &= ~(0x3 << 62)
    value |= (0x2 << 62)
    return uuid.UUID(int=value)


# 预计算常量
_MASK_48 = (1 << 48) - 1
_MASK_CLEAR = ~(0xF << 76) & ~(0x3 << 62)
_MASK_SET = (0x7 << 76) | (0x2 << 62)

def uuid7_str() -> str:
    """
    极速 uuid7，直接返回字符串，跳过 uuid.UUID 对象创建。
    性能比 str(uuid7()) 快 2-3 倍。
    """
    value = (int(time.time() * 1000) << 80) | random.getrandbits(80)
    value = (value & _MASK_CLEAR) | _MASK_SET
    h = f'{value:032x}'
    return f'{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}'

def parse_uuid7_timestamp(uuid_str: str) -> dict:
    """
    解析 UUIDv7 字符串，返回包含时间戳信息的字典
    """
    try:
        # 1. 转换为 UUID 对象（自动处理格式验证）
        u = uuid.UUID(uuid_str)
        
        # 2. 检查版本是否为 7
        if u.version != 7:
            raise ValueError(f"该 UUID 版本为 {u.version}，不是 v7")

        # 3. 提取时间戳
        # UUID 总共 128 位，前 48 位是时间戳
        # 这里的 int 是 128 位的整数，右移 80 位即可拿到高 48 位
        ts_ms = u.int >> 80
        
        # 4. 转换为秒 (float)
        ts_seconds = ts_ms / 1000.0
        
        # 5. 生成 datetime 对象
        dt_local = datetime.fromtimestamp(ts_seconds)
        
        return {
            "timestamp_ms": ts_ms,
            "datetime_local": dt_local,
            "iso_format": dt_local.isoformat()
        }

    except ValueError as e:
        return {"error": str(e)}




if __name__ == '__main__':
    # 验证输出格式
    print("uuid7():", uuid7())
    print("uuid7_fast():", uuid7_fast())
    print("uuid7_str():", uuid7_str())
    print("解析验证:", parse_uuid7_timestamp(uuid7_str()))
    
    n = 1000000
    print(f"\n=== 性能对比 ({n} 次) ===")
    
    # str(uuid7()) - 原版
    t = time.time()
    for _ in range(n):
        str(uuid7())
    print(f"str(uuid7()):      {time.time()-t:.3f} 秒")
    
    # str(uuid7_fast()) - random版
    t = time.time()
    for _ in range(n):
        str(uuid7_fast())
    print(f"str(uuid7_fast()): {time.time()-t:.3f} 秒")
    
    # uuid7_str() - 极速版
    t = time.time()
    for _ in range(n):
        uuid7_str()
    print(f"uuid7_str():       {time.time()-t:.3f} 秒  ← 最快")