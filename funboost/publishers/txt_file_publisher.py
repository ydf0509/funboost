# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 12:12
import shutil
from pathlib import Path

from nb_filelock import FileLock
from persistqueue import Queue
from persistqueue.serializers import json as json_serializer

from funboost import funboost_config_deafult
from funboost.publishers.base_publisher import AbstractPublisher


class TxtFilePublisher(AbstractPublisher, ):
    """
    使用txt文件作为中间件
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._file_queue_path = str((Path(funboost_config_deafult.TXT_FILE_PATH) / self.queue_name).absolute())
        # Path(self._file_queue_path).mkdir(exist_ok=True)
        self.file_queue = Queue(self._file_queue_path,
                                autosave=True, serializer=json_serializer)
        self._file_lock = FileLock(Path(self._file_queue_path) / '_fsdf_queue.lock')

    def concrete_realization_of_publish(self, msg):
        with self._file_lock:
            self.file_queue.put(msg)

    def clear(self):
        shutil.rmtree(self._file_queue_path, ignore_errors=True)
        self.logger.warning(f'清除 {Path(self._file_queue_path).absolute()} 文件夹成功')

    def get_message_count(self):
        return self.file_queue.qsize()

    def close(self):
        pass
