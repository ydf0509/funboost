from funboost.consumers.celery_consumer import CeleryHelper

CeleryHelper.start_flower(port=5557)  # 启动flower 网页，这个函数也可以单独的脚本中启动