# import gevent.monkey;gevent.monkey.patch_all()
import copy
import time
import typing

from funboost import boost, BrokerEnum,ConcurrentModeEnum,BoosterParams,ctrl_c_recv,AbstractConsumer
import nb_log
import json

from funboost.core.current_task import funboost_current_task
from funboost.core.function_result_status_saver import FunctionResultStatus, RunStatus
from funboost.core.helper_funs import delete_keys_and_return_new_dict
from funboost.core.serialization import Serialization
from funboost.utils.redis_manager import RedisMixin
from funboost.consumers.base_consumer import *

logger = nb_log.get_logger('sdsda',is_add_stream_handler=False,log_filename='xxx.log')
class MostFastConsumer(AbstractConsumer):
    pass

    def _convert_msg_before_run(self, msg: typing.Union[str, dict]) -> dict:
        """
        转换消息,消息没有使用funboost来发送,并且没有extra相关字段时候
        用户也可以按照4.21文档,继承任意Consumer类,并实现方法 _user_convert_msg_before_run,先转换不规范的消息.
        """
        """ 一般消息至少包含这样
        {
          "a": 42,
          "b": 84,
          "extra": {
            "task_id": "queue_2_result:9b79a372-f765-4a33-8639-9d15d7a95f61",
            "publish_time": 1701687443.3596,
            "publish_time_format": "2023-12-04 18:57:23"
          }
        }
        """

        """
        extra_params = {'task_id': task_id, 'publish_time': round(time.time(), 4),
                        'publish_time_format': time.strftime('%Y-%m-%d %H:%M:%S')}
        """
        msg = self._user_convert_msg_before_run(msg)
        msg = Serialization.to_dict(msg)
        # 以下是清洗补全字段.
        if 'extra' not in msg:
            msg['extra'] = {'is_auto_fill_extra': True}
        extra = msg['extra']
        if 'task_id' not in extra:
            extra['task_id'] = MsgGenerater.generate_task_id(self._queue_name)
        if 'publish_time' not in extra:
            extra['publish_time'] = MsgGenerater.generate_publish_time()
        if 'publish_time_format':
            extra['publish_time_format'] = MsgGenerater.generate_publish_time_format()
            # extra['publish_time_format'] =  time.strftime('%Y-%m-%d %H:%M:%S')
        return msg

    
    # def _submit_task(self, kw):
    #     body_dict = json.loads(kw['body'])
    #     if body_dict['x']%10000 == 0:
    #         print(body_dict['x'])
    #         return
    #     else:
    #         return

    def _submit_task(self, kw):
        # body_dict = json.loads(kw['body'])
        # kw['body'] = body_dict
        # if body_dict['x']%10000 == 0:
        #     print(body_dict['x'])
        #     return
        # else:
        #     return
        
        kw['body'] = self._convert_msg_before_run(kw['body'])
        self._print_message_get_from_broker(kw['body'])
        if self._judge_is_daylight():
            self._requeue(kw)
            time.sleep(self.time_interval_for_check_do_not_run_time)
            return
        function_only_params = delete_keys_and_return_new_dict(kw['body'], )
        if self._get_priority_conf(kw, 'do_task_filtering') and self._redis_filter.check_value_exists(
                function_only_params,self._get_priority_conf(kw, 'filter_str')):  # 对函数的参数进行检查，过滤已经执行过并且成功的任务。
            self.logger.warning(f'redis的 [{self._redis_filter_key_name}] 键 中 过滤任务 {kw["body"]}')
            self._confirm_consume(kw) # 不运行就必须确认消费，否则会发不能确认消费，导致消息队列中间件认为消息没有被消费。
            return
        # publish_time = get_publish_time(kw['body'])
        publish_time = 0
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
            run_date = FunboostTime(kw['body']['extra']['publish_time']).datetime_obj + datetime.timedelta(seconds=msg_countdown)
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
                                               kwargs={'queue_name': self.queue_name, 'msg': msg_no_delay, },
                                               misfire_grace_time=misfire_grace_time,
                                              )
            self._confirm_consume(kw)

        else:  # 普通任务
            self.concurrent_pool.submit(self._run, kw)

        if self.consumer_params.is_using_distributed_frequency_control:  # 如果是需要分布式控频。
            active_num = self._distributed_consumer_statistics.active_consumer_num
            self._frequency_control(self.consumer_params.qps / active_num, self._msg_schedule_time_intercal * active_num)
        else:
            self._frequency_control(self.consumer_params.qps, self._msg_schedule_time_intercal)

        while 1:  # 这一块的代码为支持暂停消费。
            # print(self._pause_flag)
            if self._pause_flag.is_set():
                if time.time() - self._last_show_pause_log_time > 60:
                    self.logger.warning(f'已设置 {self.queue_name} 队列中的任务为暂停消费')
                    self._last_show_pause_log_time = time.time()
                time.sleep(5)
            else:
                break


    def _run(self, kw: dict, ):
        # print(kw)
        # body_dict = kw['body']
        # if body_dict['x']%10000 == 0:
        #     print(body_dict['x'])
        #     return
        # else:
        #     return
        
        try:
            t_start_run_fun = time.time()
            max_retry_times = self._get_priority_conf(kw, 'max_retry_times')
            current_function_result_status = FunctionResultStatus(self.queue_name, self.consuming_function.__name__, kw['body'], )
            current_retry_times = 0
            function_only_params = delete_keys_and_return_new_dict(kw['body'])
            for current_retry_times in range(max_retry_times + 1):
                current_function_result_status.run_times = current_retry_times + 1
                current_function_result_status.run_status = RunStatus.running
                self._result_persistence_helper.save_function_result_to_mongo(current_function_result_status)
                current_function_result_status = self._run_consuming_function_with_confirm_and_retry(kw, current_retry_times=current_retry_times,
                                                                                                     function_result_status=current_function_result_status)
                if (current_function_result_status.success is True or current_retry_times == max_retry_times
                        or current_function_result_status._has_requeue
                        or current_function_result_status._has_to_dlx_queue
                        or current_function_result_status._has_kill_task):
                    break
                else:
                    if self.consumer_params.retry_interval:
                        time.sleep(self.consumer_params.retry_interval)
            if not (current_function_result_status._has_requeue and self.BROKER_KIND in [BrokerEnum.RABBITMQ_AMQPSTORM, BrokerEnum.RABBITMQ_PIKA, BrokerEnum.RABBITMQ_RABBITPY]):  # 已经nack了，不能ack，否则rabbitmq delevar tag 报错
                self._confirm_consume(kw)
            current_function_result_status.run_status = RunStatus.finish
            self._result_persistence_helper.save_function_result_to_mongo(current_function_result_status)
            if self._get_priority_conf(kw, 'do_task_filtering'):
                self._redis_filter.add_a_value(function_only_params,self._get_priority_conf(kw, 'filter_str'))  # 函数执行成功后，添加函数的参数排序后的键值对字符串到set中。
            if current_function_result_status.success is False and current_retry_times == max_retry_times:
                log_msg = f'函数 {self.consuming_function.__name__} 达到最大重试次数 {self._get_priority_conf(kw, "max_retry_times")} 后,仍然失败， 入参是  {function_only_params} '
                if self.consumer_params.is_push_to_dlx_queue_when_retry_max_times:
                    log_msg += f'  。发送到死信队列 {self._dlx_queue_name} 中'
                    self.publisher_of_dlx_queue.publish(kw['body'])
                # self.logger.critical(msg=f'{log_msg} \n', )
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)

            if self._get_priority_conf(kw, 'is_using_rpc_mode'):
                # print(function_result_status.get_status_dict(without_datetime_obj=
                if (current_function_result_status.success is False and current_retry_times == max_retry_times) or current_function_result_status.success is True:
                    with RedisMixin().redis_db_filter_and_rpc_result.pipeline() as p:
                        # RedisMixin().redis_db_frame.lpush(kw['body']['extra']['task_id'], json.dumps(function_result_status.get_status_dict(without_datetime_obj=True)))
                        # RedisMixin().redis_db_frame.expire(kw['body']['extra']['task_id'], 600)
                        current_function_result_status.rpc_result_expire_seconds = self.consumer_params.rpc_result_expire_seconds
                        p.lpush(kw['body']['extra']['task_id'],
                                Serialization.to_json_str(current_function_result_status.get_status_dict(without_datetime_obj=True)))
                        p.expire(kw['body']['extra']['task_id'], self.consumer_params.rpc_result_expire_seconds)
                        p.execute()

            with self._lock_for_count_execute_task_times_every_unit_time:
                self.metric_calculation.cal(t_start_run_fun,current_function_result_status)
            self._frame_custom_record_process_info_func(current_function_result_status,kw)
            self.user_custom_record_process_info_func(current_function_result_status,)  # 两种方式都可以自定义,记录结果,建议继承方式,不使用boost中指定 user_custom_record_process_info_func
            if self.consumer_params.user_custom_record_process_info_func:
                self.consumer_params.user_custom_record_process_info_func(current_function_result_status,)
        except BaseException as e:
            log_msg = f' error 严重错误 {type(e)} {e} '
            # self.logger.critical(msg=f'{log_msg} \n', exc_info=True)
            # self.error_file_logger.critical(msg=f'{log_msg} \n', exc_info=True)
            self.logger.critical(msg=log_msg, exc_info=True)
        # fct = funboost_current_task()
        # fct.set_fct_context(None)
    

     # noinspection PyProtectedMember
    def _run_consuming_function_with_confirm_and_retry(self, kw: dict, current_retry_times,
                                                       function_result_status: FunctionResultStatus, ):
        function_only_params = delete_keys_and_return_new_dict(kw['body']) if self._do_not_delete_extra_from_msg is False else kw['body']
        task_id = kw['body']['extra']['task_id']
        t_start = time.time()

        # fct = funboost_current_task()
        # fct_context = FctContext(function_params=function_only_params,
        #                          full_msg=kw['body'],
        #                          function_result_status=function_result_status,
        #                          logger=self.logger, queue_name=self.queue_name,)

        try:
            function_run = self.consuming_function
            if self._consuming_function_is_asyncio:
                # fct_context.asyncio_use_thread_concurrent_mode = True
                function_run = sync_or_async_fun_deco(function_run)
            else:
                pass
                # fct_context.asynco_use_thread_concurrent_mode = False
            # fct.set_fct_context(fct_context)
            function_timeout = self._get_priority_conf(kw, 'function_timeout')
            function_run = function_run if self.consumer_params.consumin_function_decorator is None else self.consumer_params.consumin_function_decorator(function_run)
            function_run = function_run if not function_timeout else self._concurrent_mode_dispatcher.timeout_deco(
                function_timeout)(function_run)

            if self.consumer_params.is_support_remote_kill_task:
                if kill_remote_task.RemoteTaskKiller(self.queue_name, task_id).judge_need_revoke_run():  # 如果远程指令杀死任务，如果还没开始运行函数，就取消运行
                    function_result_status._has_kill_task = True
                    self.logger.warning(f'取消运行 {task_id} {function_only_params}')
                    return function_result_status
                function_run = kill_remote_task.kill_fun_deco(task_id)(function_run)  # 用杀死装饰器包装起来在另一个线程运行函数,以便等待远程杀死。
            function_result_status.result = function_run(**self._convert_real_function_only_params_by_conusuming_function_kind(function_only_params,kw['body']['extra']))
            # if asyncio.iscoroutine(function_result_status.result):
            #     log_msg = f'''异步的协程消费函数必须使用 async 并发模式并发,请设置消费函数 {self.consuming_function.__name__} 的concurrent_mode 为 ConcurrentModeEnum.ASYNC 或 4'''
            #     # self.logger.critical(msg=f'{log_msg} \n')
            #     # self.error_file_logger.critical(msg=f'{log_msg} \n')
            #     self._log_critical(msg=log_msg)
            #     # noinspection PyProtectedMember,PyUnresolvedReferences
            #
            #     os._exit(4)
            function_result_status.success = True
            if self.consumer_params.log_level <= logging.DEBUG:
                result_str_to_be_print = str(function_result_status.result)[:100] if len(str(function_result_status.result)) < 100 else str(function_result_status.result)[:100] + '  。。。。。  '
                # print(funboost_current_task().task_id)
                # print(fct.function_result_status.task_id)
                # print(get_current_taskid())
                self.logger.debug(f' 函数 {self.consuming_function.__name__}  '
                                  f'第{current_retry_times + 1}次 运行, 正确了，函数运行时间是 {round(time.time() - t_start, 4)} 秒,入参是 {function_only_params} , '
                                  f'结果是  {result_str_to_be_print}   {self._get_concurrent_info()}  ')
        except BaseException as e:
            if isinstance(e, (ExceptionForRequeue,)):  # mongo经常维护备份时候插入不了或挂了，或者自己主动抛出一个ExceptionForRequeue类型的错误会重新入队，不受指定重试次数逇约束。
                log_msg = f'函数 [{self.consuming_function.__name__}] 中发生错误 {type(e)}  {e} 。消息重新放入当前队列 {self._queue_name}'
                # self.logger.critical(msg=f'{log_msg} \n')
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)
                time.sleep(0.1)  # 防止快速无限出错入队出队，导致cpu和中间件忙
                # 重回队列如果不修改task_id,insert插入函数消费状态结果到mongo会主键重复。要么保存函数消费状态使用replace，要么需要修改taskikd
                # kw_new = copy.deepcopy(kw)
                # new_task_id =f'{self._queue_name}_result:{uuid.uuid4()}'
                # kw_new['body']['extra']['task_id'] = new_task_id
                # self._requeue(kw_new)
                self._requeue(kw)
                function_result_status._has_requeue = True
            if isinstance(e, ExceptionForPushToDlxqueue):
                log_msg = f'函数 [{self.consuming_function.__name__}] 中发生错误 {type(e)}  {e}，消息放入死信队列 {self._dlx_queue_name}'
                # self.logger.critical(msg=f'{log_msg} \n')
                # self.error_file_logger.critical(msg=f'{log_msg} \n')
                self.logger.critical(msg=log_msg)
                self.publisher_of_dlx_queue.publish(kw['body'])  # 发布到死信队列，不重回当前队列
                function_result_status._has_to_dlx_queue = True
            if isinstance(e, kill_remote_task.TaskHasKilledError):
                log_msg = f'task_id 为 {task_id} , 函数 [{self.consuming_function.__name__}] 运行入参 {function_only_params}   ，已被远程指令杀死 {type(e)}  {e}'
                # self.logger.critical(msg=f'{log_msg} ')
                # self.error_file_logger.critical(msg=f'{log_msg} ')
                self.logger.critical(msg=log_msg)
                function_result_status._has_kill_task = True
            if isinstance(e, (ExceptionForRequeue, ExceptionForPushToDlxqueue, kill_remote_task.TaskHasKilledError)):
                return function_result_status
            log_msg = f'''函数 {self.consuming_function.__name__}  第{current_retry_times + 1}次运行发生错误，
                          函数运行时间是 {round(time.time() - t_start, 4)} 秒,  入参是  {function_only_params}    
                          {type(e)} {e} '''
            # self.logger.error(msg=f'{log_msg} \n', exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            # self.error_file_logger.error(msg=f'{log_msg} \n', exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            self.logger.error(msg=log_msg, exc_info=self._get_priority_conf(kw, 'is_print_detail_exception'))
            # traceback.print_exc()
            function_result_status.exception = f'{e.__class__.__name__}    {str(e)}'
            function_result_status.exception_msg = str(e)
            function_result_status.exception_type = e.__class__.__name__

            function_result_status.result = FunctionResultStatus.FUNC_RUN_ERROR
        return function_result_status



     


@BoosterParams(queue_name='test_speed_queuex', broker_kind=BrokerEnum.REDIS, 
               concurrent_num=2, log_level=20,
                     qps=0, concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD, 
                     is_auto_start_consuming_message=False,
                     broker_exclusive_config={'pull_msg_batch_size':100},
                    #  consumer_override_cls=MostFastConsumer,
                     )
def f_test_speed(x):
    pass
    # logger.debug(x)
    # f_test_speed2.push(x * 10)
    if x% 1000 == 0:
        print(x)
    # time.sleep(20)



# @boost('speed_test_queue2', broker_kind=BrokerEnum.REDIS, log_level=20, qps=2)
# def f_test_speed2(y):
#     pass
#     print(y)


if __name__ == '__main__':
    # f_test_speed.clear()

    for i in range(200000):
        if i % 1000 == 0:
            print(f'发布任务 {i}')
        f_test_speed.push(i)
    f_test_speed.consume()
    ctrl_c_recv()



    # f_test_speed.multi_process_consume(2)
    # # f_test_speed2.consume()
