import sys
from pathlib import Path

current_dir = str(Path(__file__).parent)

sys.path.insert(4, current_dir) # 这样做是为了提高这里的优先级，例如用户自己安装了aioredis包，但是运行funboost时候，这个文件夹的aioredis包会优先被导入，比sys.path.append好。
# sys.path.append(current_dir)
