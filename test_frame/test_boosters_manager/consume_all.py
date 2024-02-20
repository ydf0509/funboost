import queue_names
from funboost import BoostersManager
import mod1, mod2  # 这个是必须导入的,可以不用,但必须导入,这样BoostersManager才能知道相关模块中的@boost装饰器

# 选择启动哪些队列名消费
# BoostersManager.consume(queue_names.q_test_queue_manager1,queue_names.q_test_queue_manager2a)

# 选择启动哪些队列名消费,每个队列设置不同的消费进程数量
BoostersManager.m_consume(**{queue_names.q_test_queue_manager1: 2, queue_names.q_test_queue_manager2a: 3})

# 启动所有队列名消费,在同一个进程内消费
BoostersManager.consume_all()

# 启动所有队列名消费,每个队列启动单独的n个进程消费
# BoostersManager.m_consume_all()
