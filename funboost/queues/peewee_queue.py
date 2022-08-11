import datetime
import time

from peewee import ModelSelect
from playhouse.shortcuts import model_to_dict, dict_to_model

from nb_log import LoggerMixin, LoggerLevelSetterMixin
from funboost import funboost_config_deafult
from peewee import *



class TaskStatus:
    TO_BE_CONSUMED = 'to_be_consumed'
    PENGDING = 'pengding'
    FAILED = 'failed'
    SUCCESS = 'success'
    REQUEUE = 'requeue'


class PeeweeQueue(LoggerMixin, LoggerLevelSetterMixin):
    """
    使用peewee操作数据库模拟消息队列
    """

    def __init__(self, queue_name):
        self.queue_name = queue_name
        self.FunboostMessage = None
        self._create_table()

    def _create_table(self):
        class FunboostMessage(Model):
            """数据库的一行模拟一条消息"""
            job_id = BigAutoField(primary_key=True, )
            body = CharField(max_length=10240, null=False)
            publish_timestamp = DateTimeField(default=datetime.datetime.now)
            status = CharField(max_length=40, null=False)
            consume_start_timestamp = DateTimeField(default=None, null=True)

            class Meta:
                db_table = self.queue_name
                conn_params = dict(
                    host=funboost_config_deafult.MYSQL_HOST,
                    port=funboost_config_deafult.MYSQL_PORT,
                    user=funboost_config_deafult.MYSQL_USER,
                    passwd=funboost_config_deafult.MYSQL_PASSWORD,
                    database=funboost_config_deafult.MYSQL_DATABASE,
                )
                database = MySQLDatabase(**conn_params)

        FunboostMessage.create_table()
        self.FunboostMessage = FunboostMessage

    def push(self, body):
        msg = self.FunboostMessage(body=body, status=TaskStatus.TO_BE_CONSUMED, consume_start_timestamp=None)
        msg.save()

    def get(self):
        while True:
            ten_minitues_ago_datetime = datetime.datetime.now() + datetime.timedelta(minutes=-10)
            ret = self.FunboostMessage.select().where(self.FunboostMessage.status.in_([TaskStatus.TO_BE_CONSUMED, TaskStatus.REQUEUE])
                                                      | (
                                                              (self.FunboostMessage.status == TaskStatus.PENGDING) &
                                                              (self.FunboostMessage.consume_start_timestamp < ten_minitues_ago_datetime)
                                                      )).limit(1)
            # ret = self.FunboostMessage.select().where(self.FunboostMessage.status=='dsadsad').limit(1)
            # print(ret)
            if len(ret) == 1:
                row_obj = ret[0]
                row = model_to_dict(row_obj)
                self.FunboostMessage.update(status=TaskStatus.PENGDING, consume_start_timestamp=datetime.datetime.now()
                                            ).where(self.FunboostMessage.job_id == row['job_id']).execute()
                return row
            else:
                time.sleep(0.2)

    def set_success(self, job_id, is_delete_the_task=False):
        if is_delete_the_task:
            self.FunboostMessage.delete_by_id(job_id)
        else:
            # ModelSelect.for_update()
            # print(self.FunboostMessage.update(status=TaskStatus.SUCCESS).where(self.FunboostMessage.job_id==job_id))
            self.FunboostMessage.update(status=TaskStatus.SUCCESS).where(self.FunboostMessage.job_id == job_id).execute()

    def set_failed(self, job_id, ):
        self.set_task_status(job_id, status=TaskStatus.FAILED)

    def set_task_status(self, job_id, status: str):
        self.FunboostMessage.update(status=status).where(self.FunboostMessage.job_id == job_id).execute()

    def requeue_task(self, job_id):
        self.set_task_status(job_id, TaskStatus.REQUEUE)

    def clear_queue(self):
        self.FunboostMessage.truncate_table()

    def get_count_by_status(self, status):
        return self.FunboostMessage.select().where(self.FunboostMessage.status == status).count()

    @property
    def total_count(self):
        return self.FunboostMessage.select().count()

    @property
    def to_be_consumed_count(self):
        return self.get_count_by_status(TaskStatus.TO_BE_CONSUMED)


if __name__ == '__main__':
    from threadpool_executor_shrink_able import ThreadPoolExecutorShrinkAble
    q = PeeweeQueue('peewee_queue')
    q.set_success(1)

    pool = ThreadPoolExecutorShrinkAble(20)
    # q.clear_queue()
    # t1 = time.time()
    #
    # for i in range(10000):
    #     # q.push(body=f'{{"a":{i}}}',status=TaskStatus.TO_BE_CONSUMED)
    #     pool.submit(q.push, body=f'{{"a":{i}}}', status=TaskStatus.TO_BE_CONSUMED)
    # # q.get()
    # # q.set_success(3,is_delete_the_task=False)
    # pool.shutdown()
    # print(time.time() - t1)
    # print(q.total_count)
