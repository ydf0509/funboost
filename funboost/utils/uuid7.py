
"""
python3.7 没有uuid7，自己实现。

uuid7比uuid4对数据库更友好，类似雪花算法

UUIDv4 完全无法知道生成时间；
UUIDv7 可以精确还原生成时间（毫秒级）。
"""

import time
import secrets
import uuid
import datetime

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
    uuid7_str = str(uuid7())
    print(uuid7_str)
    print(parse_uuid7_timestamp(uuid7_str))