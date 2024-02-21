from pathlib import Path

import queue_names
from funboost import BoostersManager, BoosterDiscovery

# import mod1, mod2  # 这个是必须导入的,可以不用,但必须导入,这样BoostersManager才能知道相关模块中的@boost装饰器,或者用下面的 BoosterDiscovery.auto_discovery()来自动导入m1和m2模块.


if __name__ == '__main__':
    BoosterDiscovery(project_root_path=Path(__file__).parent.parent.parent, booster_dirs=[Path(__file__).parent]).auto_discovery()  # 这个放在main里面运行,防止无限懵逼死循环
    for x in range(10):
        BoostersManager.push(queue_names.Q_TEST_QUEUE_MANAGER1, x)
        BoostersManager.push(queue_names.Q_TEST_QUEUE_MANAGER2A, x * 20)
        BoostersManager.publish(queue_names.Q_TEST_QUEUE_MANAGER2B, {'x': x * 300})
