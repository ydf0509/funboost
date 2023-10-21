# # -*- coding: utf-8 -*-
# # @Author  : ydf
# # @Time    : 2022/8/8 0008 13:32
# import threading
#
# from functools import partial
#
# from funboost import funboost_config_deafult
#
# from funboost.consumers.base_consumer import AbstractConsumer
# import celery
#
#
# class CeleryConsumer(AbstractConsumer):
#     """
#     celery作为中间件实现的。
#     """
#     BROKER_KIND = 30
#     BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'celery_app_config': {}}
#
#     # celery的可以配置项大全  https://docs.celeryq.dev/en/stable/userguide/configuration.html#new-lowercase-settings
#
#     def _shedual_task(self):
#         raw_fun = self.consuming_function
#
#         celery_app = celery.Celery(broker=funboost_config_deafult.CELERY_BROKER_URL,
#                                    backend=funboost_config_deafult.CELERY_RESULT_BACKEND,
#                                    task_routes={},timezone=funboost_config_deafult.TIMEZONE,enable_utc=False)
#         celery_app.config_from_object(self.broker_exclusive_config['celery_app_config'])
#         celery_app.conf.task_routes.update({self.queue_name: {"queue": self.queue_name}})
#
#         celery_app.conf.task_reject_on_worker_lost = True  # 配置这两项可以随意停止
#         celery_app.conf.task_acks_late = True
#
#         # celery_app.conf.worker_task_log_format = '%(asctime)s - %(name)s - "%(pathname)s:%(lineno)d" - %(funcName)s - %(levelname)s - %(message)s'
#         # celery_app.conf.worker_log_format = '%(asctime)s - %(name)s - "%(pathname)s:%(lineno)d" - %(funcName)s - %(levelname)s - %(message)s'
#
#         celery_app.conf.worker_redirect_stdouts = False
#
#         @celery_app.task(name=self.queue_name)
#         def f(*args, **kwargs):
#             # func_params = json.loads(msg)
#             # func_params.pop('extra')
#             # return raw_fun(**func_params)
#             # print(args)
#             # print(kwargs)
#             self.logger.debug(f' 这条消息将由 funboost 在 celery 框架中处理: args:  {args} ,  kwargs: {kwargs}')
#             return raw_fun(*args, **kwargs)
#
#         # celery_app.worker_main(
#         #     argv=['worker', '--pool=threads', '--concurrency=500', '-n', 'worker1@%h', '--loglevel=INFO',
#         #           f'--queues={self.queue_name}',
#         #           ])
#
#         # logging.getLevelName(self._log_level)
#         celery_app.worker_main(
#             argv=['worker', '--pool=threads', f'--concurrency={self._concurrent_num}',
#                   '-n', f'worker_{self.queue_name}@%h', f'--loglevel=INFO',
#                   f'--queues={self.queue_name}',
#                   ])
#
#         # worker = celery_app.Worker()
#         # worker.start()
#
#     def _confirm_consume(self, kw):
#         pass
#
#     def _requeue(self, kw):
#         pass
#
#
# class CeleryBeatHelper:
#     def __init__(self, beat_schedule: dict):
#         '''
#
#         celery_app.conf.beat_schedule = {
#     'add-every-30-seconds': {
#         'task': '求和啊',
#         'schedule': timedelta(seconds=2),
#         'args': (10000, 20000)
#     }}
#         :param beat_schedule:
#         '''
#         self.beat_schedule = beat_schedule
#         self.celery_app = None
#
#     def get_celery_app(self):
#         celery_app = celery.Celery(broker=funboost_config_deafult.CELERY_BROKER_URL,
#                                    backend=funboost_config_deafult.CELERY_RESULT_BACKEND,
#                                    task_routes={},timezone=funboost_config_deafult.TIMEZONE,enable_utc=False)
#
#         for k, v in self.beat_schedule.items():
#             queue_name = v['task']
#
#             @celery_app.task(name=queue_name)
#             def f(*args, **kwargs):
#                 pass
#
#             celery_app.conf.task_routes.update({queue_name: {"queue": queue_name}})
#         celery_app.conf.beat_schedule = self.beat_schedule
#         # celery_app.worker_main(
#         #     argv=['worker','beat',
#         #           f'--loglevel=INFO',
#         #           ])
#         self.celery_app = celery_app
#         return celery_app
#
#     def start_beat(self):
#         '''
#         celery -A test_celery_beat beat
#         '''
#         beat = partial(self.celery_app.Beat, loglevel='INFO',
#                        )
#         beat().run()
#
#
# def celery_start_beat(beat_schedule: dict):
#     def _f():
#         celery_beat_helper = CeleryBeatHelper(beat_schedule)
#         celery_app = celery_beat_helper.get_celery_app()
#         celery_beat_helper.start_beat()
#     threading.Thread(target=_f).start() # 使得可以很方便启动定时任务，继续启动函数消费
