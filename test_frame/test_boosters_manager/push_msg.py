import queue_names
from funboost import BoostersManager
import mod1, mod2  # 这个是必须导入的,可以不用,但必须导入,这样BoostersManager才能知道相关模块中的@boost装饰器

if __name__ == '__main__':
    for x in range(10):
        BoostersManager.push(queue_names.q_test_queue_manager1, x)
        BoostersManager.push(queue_names.q_test_queue_manager2a, x * 20)
        BoostersManager.publish(queue_names.q_test_queue_manager2b, {'x': x * 300})
