from pathlib import Path

from nb_filelock import FileLock
from persistqueue import Queue
import json
from persistqueue.serializers import json as json_serializer
from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost import funboost_config_deafult


class TxtFileConsumer(AbstractConsumer, ):
    """
    txt文件作为消息队列
    这个不想做消费确认了,要消费确认请选 SQLITE_QUEUE 、PERSISTQUEUE中间件
    """

    def _shedual_task(self):
        file_queue_path = str((Path(funboost_config_deafult.TXT_FILE_PATH) / self.queue_name).absolute())
        file_lock = FileLock(Path(file_queue_path) / f'_funboost_txtfile_{self.queue_name}.lock')
        queue = Queue(str((Path(funboost_config_deafult.TXT_FILE_PATH) / self.queue_name).absolute()), autosave=True, serializer=json_serializer)
        while True:
            with file_lock:
                item = queue.get()
                self._print_message_get_from_broker('txt文件', item)
                kw = {'body': json.loads(item), 'q': queue, 'item': item}
                self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass
        # kw['q'].task_done()

    def _requeue(self, kw):
        pass
        # kw['q'].nack(kw['item'])
