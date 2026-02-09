import queue


class PythonQueues:
    local_pyhton_queue_name__local_pyhton_queue_obj_map  = {}

    @classmethod
    def get_queue(cls, queue_name, maxsize=0):
        """
        获取或创建一个内存队列
        
        :param queue_name: 队列名称
        :param maxsize: 队列最大容量，0表示无界队列（默认），正整数表示有界队列
                       当队列已满时，put操作会阻塞直到有空位
        :return: queue.Queue 对象
        """
        if queue_name not in cls.local_pyhton_queue_name__local_pyhton_queue_obj_map:
            cls.local_pyhton_queue_name__local_pyhton_queue_obj_map[queue_name] = queue.Queue(maxsize=maxsize)
        return cls.local_pyhton_queue_name__local_pyhton_queue_obj_map[queue_name]