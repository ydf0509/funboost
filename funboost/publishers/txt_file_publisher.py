# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import shutil
from pathlib import Path

from nb_filelock import FileLock
from persistqueue import Queue
from persistqueue.serializers import json as json_serializer

from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.base_publisher import AbstractPublisher


class TxtFilePublisher(AbstractPublisher, ):
    """
    使用txt文件作为中间件
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._file_queue_path = str((Path(BrokerConnConfig.TXT_FILE_PATH) / self.queue_name).absolute())
        # Path(self._file_queue_path).mkdir(exist_ok=True)
        self.file_queue = Queue(self._file_queue_path,
                                autosave=True, serializer=json_serializer)
        self._file_lock = FileLock(Path(self._file_queue_path) / f'_funboost_txtfile_{self.queue_name}.lock')

    def _publish_impl(self, msg):
        with self._file_lock:
            self.file_queue.put(msg)

    def clear(self):
        shutil.rmtree(self._file_queue_path, ignore_errors=True)
        self.logger.warning(f'清除 {Path(self._file_queue_path).absolute()} 文件夹成功')

    def get_message_count(self):
        return self.file_queue.qsize()

    def close(self):
        pass
