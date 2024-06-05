import threading

from funboost.core.current_task import thread_current_task


class FctThread(threading.Thread):
    thread_current_task__dict_key = 'thread_current_task__dict'


    def run(self):
        thread_current_task._fct_local_data.__dict__.update(getattr(self,self.thread_current_task__dict_key))  # 把funboost的消费线程上下文需要传递到线程上下文里面来.
        super().run()
