from cashews import cache
import time

# 注意：确保你的环境安装了 redis
cache.setup("redis://127.0.0.1:6379")

@cache.callable(ttl="10s", lock=True)
def get_data(name):
    print("--- 正在执行同步查询 ---")
    time.sleep(2)
    return {"status": 1, "name": name}

if __name__ == "__main__":
    # 这样调用在很多版本中可以兼容同步
    print(get_data("test"))