import copy
import datetime
import threading
import time
import uuid

from funboost import AbstractConsumer
from funboost.core.funboost_time import FunboostTime
from funboost.core.helper_funs import delete_keys_and_return_new_dict, get_publish_time


class PauseConsumer(AbstractConsumer):
    pause = threading.Event()

    def _submit_task(self, kw):
        
        kw['body'] = self.convert_msg_before_run(kw['body'])
        self._print_message_get_from_broker(kw['body'])
        if self._judge_is_daylight():
            self._requeue(kw)
            time.sleep(self.time_interval_for_check_do_not_run_time)
            return
        function_only_params = delete_keys_and_return_new_dict(kw['body'], )
        if self._get_priority_conf(kw, 'do_task_filtering') and self._redis_filter.check_value_exists(
                function_only_params):  # 对函数的参数进行检查，过滤已经执行过并且成功的任务。
            self.logger.warning(f'redis的 [{self._redis_filter_key_name}] 键 中 过滤任务 {kw["body"]}')
            self._confirm_consume(kw)
            return
        publish_time = get_publish_time(kw['body'])
        msg_expire_senconds_priority = self._get_priority_conf(kw, 'msg_expire_senconds')
        if msg_expire_senconds_priority and time.time() - msg_expire_senconds_priority > publish_time:
            self.logger.warning(
                f'消息发布时戳是 {publish_time} {kw["body"].get("publish_time_format", "")},距离现在 {round(time.time() - publish_time, 4)} 秒 ,'
                f'超过了指定的 {msg_expire_senconds_priority} 秒，丢弃任务')
            self._confirm_consume(kw)
            return 0

        msg_eta = self._get_priority_conf(kw, 'eta')
        msg_countdown = self._get_priority_conf(kw, 'countdown')
        misfire_grace_time = self._get_priority_conf(kw, 'misfire_grace_time')
        run_date = None
        # print(kw)
        if msg_countdown:
            run_date = FunboostTime(kw['body']['extra']['publish_time']).datetime_obj + datetime.timedelta(
                seconds=msg_countdown)
        if msg_eta:
            run_date = FunboostTime(msg_eta).datetime_obj
        # print(run_date,time_util.DatetimeConverter().datetime_obj)
        # print(run_date.timestamp(),time_util.DatetimeConverter().datetime_obj.timestamp())
        # print(self.concurrent_pool)
        if run_date:  # 延时任务
            # print(repr(run_date),repr(datetime.datetime.now(tz=pytz.timezone(frame_config.TIMEZONE))))
            if self._has_start_delay_task_scheduler is False:
                self._has_start_delay_task_scheduler = True
                self._start_delay_task_scheduler()

            # 这种方式是扔到线程池
            # self._delay_task_scheduler.add_job(self.concurrent_pool.submit, 'date', run_date=run_date, args=(self._run,), kwargs={'kw': kw},
            #                                    misfire_grace_time=misfire_grace_time)

            # 这种方式是延时任务重新以普通任务方式发送到消息队列
            msg_no_delay = copy.deepcopy(kw['body'])
            self.__delete_eta_countdown(msg_no_delay)
            # print(msg_no_delay)
            # 数据库作为apscheduler的jobstores时候， 不能用 self.pbulisher_of_same_queue.publish，self不能序列化
            self._delay_task_scheduler.add_job(self._push_apscheduler_task_to_broker, 'date', run_date=run_date,
                                               kwargs={'queue_name': self.queue_name, 'msg': msg_no_delay,
                                                       'runonce_uuid': str(uuid.uuid4())},
                                               misfire_grace_time=misfire_grace_time,
                                               )
            self._confirm_consume(kw)

        else:  # 普通任务
            self.concurrent_pool.submit(self._run, kw)

        if self.consumer_params.is_using_distributed_frequency_control:  # 如果是需要分布式控频。
            active_num = self._distributed_consumer_statistics.active_consumer_num
            self._frequency_control(self.consumer_params.qps / active_num,
                                    self._msg_schedule_time_intercal * active_num)
        else:
            self._frequency_control(self.consumer_params.qps, self._msg_schedule_time_intercal)

        while 1:  # 这一块的代码为支持暂停消费。
            # print(self._pause_flag)
            if self._pause_flag.is_set() or PauseConsumer.pause.is_set():
                time.sleep(5)
                if time.time() - self._last_show_pause_log_time > 60:
                    self.logger.warning(f'已设置 {self.queue_name} 队列中的任务为暂停消费')
                    self._last_show_pause_log_time = time.time()
            else:
                break
