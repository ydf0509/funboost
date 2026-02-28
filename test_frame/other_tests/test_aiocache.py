

import asyncio
import logging
from aiocache import cached, Cache
from aiocache.serializers import JsonSerializer

# 配置日志，方便查看输出
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- 内存缓存示例 --------------------
@cached(
    cache=Cache.MEMORY,          # 使用内存后端
    ttl=10,                       # 缓存生存时间 10 秒
    namespace="memory_add"        # 命名空间，避免键冲突
)
async def add_memory(x: int, y: int) -> int:
    """模拟耗时计算的两数之和（内存缓存版）"""
    logger.info(f"计算 {x} + {y} ...")
    await asyncio.sleep(2)        # 模拟耗时操作（如复杂计算）
    return x + y

# -------------------- Redis 缓存示例 --------------------
@cached(
    cache=Cache.REDIS,            # 使用 Redis 后端
    endpoint="127.0.0.1",         # Redis 地址
    port=6379,                     # Redis 端口
    password=None,                 # 如有密码请填写
    ttl=30,                         # 缓存生存时间 30 秒
    serializer=JsonSerializer(),    # 使用 JSON 序列化（便于查看）
    namespace="redis_add"           # 命名空间
)
async def add_redis(x: int, y: int) -> int:
    """模拟耗时计算的两数之和（Redis 缓存版）"""
    logger.info(f"计算 {x} + {y} ...")
    await asyncio.sleep(2)
    return x + y

# -------------------- 测试主函数 --------------------
async def main():
    # 测试内存缓存
    logger.info("=== 测试内存缓存 ===")
    print(await add_memory(3, 5))   # 第一次调用，执行计算，缓存结果
    print(await add_memory(3, 5))   # 第二次调用，直接返回缓存，不执行函数体
    print(await add_memory(7, 2))   # 不同参数，重新计算并缓存

    logger.info("等待 10 秒，让内存缓存过期...")
    await asyncio.sleep(10)          # 等待内存缓存过期（ttl=10）
    print(await add_memory(3, 5))   # 缓存已过期，重新计算

    # 测试 Redis 缓存
    logger.info("\n=== 测试 Redis 缓存 ===")
    try:
        print(await add_redis(10, 20))
        print(await add_redis(10, 20))   # 命中 Redis 缓存
        print(await add_redis(5, 5))      # 新参数
    except ConnectionError as e:
        logger.error(f"Redis 连接失败，请确保 Redis 已启动: {e}")

    # 重要：关闭 Redis 连接池（如果是持久化应用，应在关闭时调用）
    # 这里因为脚本即将结束，可以省略，但在长时间运行的应用中需要管理

if __name__ == "__main__":
    asyncio.run(main())