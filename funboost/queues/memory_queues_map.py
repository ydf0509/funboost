import queue


class PythonQueues:
    local_pyhton_queue_name__local_pyhton_queue_obj_map  = {}

    @classmethod
    def get_queue(cls,queue_name):
        if queue_name not in cls.local_pyhton_queue_name__local_pyhton_queue_obj_map:
            cls.local_pyhton_queue_name__local_pyhton_queue_obj_map[queue_name] = queue.Queue()
        return cls.local_pyhton_queue_name__local_pyhton_queue_obj_map[queue_name]