import os
import time
from filelock import FileLock  # 使用 filelock 库实现进程锁
from funboost import boost, BrokerEnum, BoosterParams, EmptyConsumer, EmptyPublisher,ctrl_c_recv

class TxtFileConsumer(EmptyConsumer):
    def custom_init(self):
        """初始化，创建队列对应的 txt 文件和锁文件"""
        self.file_path = f"{self.queue_name}.txt"
        self.lock_path = f"{self.queue_name}.lock"
        self.file_lock = FileLock(self.lock_path)  # 使用文件锁
        # 如果文件不存在则创建
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                pass
                
    def _dispatch_task(self):
        """从 txt 文件中读取消息并提交任务"""
        while True:
            try:
                with self.file_lock:  # 使用文件锁保护文件操作
                    with open(self.file_path, 'r') as f:
                        lines = f.readlines()
                    if lines:
                        msg = lines[0].strip()
                        with open(self.file_path, 'w') as f:
                            f.writelines(lines[1:])
                        self._submit_task({'body': msg})
                    else:
                        time.sleep(0.1)
            except Exception as e:
                print(f"读取消息发生错误: {e}")
                time.sleep(0.1)

    def _confirm_consume(self, kw):
        """确认消费，这里简单实现"""
        pass

    def _requeue(self, kw):
        """重新入队"""
        with self.file_lock:
            with open(self.file_path, 'a') as f:
                f.write(f"{kw['body']}\n")

class TxtFilePublisher(EmptyPublisher):
    def custom_init(self):
        """初始化，创建队列对应的 txt 文件和锁文件"""
        self.file_path = f"{self.queue_name}.txt"
        self.lock_path = f"{self.queue_name}.lock"
        self.file_lock = FileLock(self.lock_path)  # 使用文件锁
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                pass

    def _publish_impl(self, msg: str):
        """发布消息到 txt 文件"""
        with self.file_lock:
            with open(self.file_path, 'a') as f:
                f.write(f"{msg}\n")

    def clear(self):
        """清空队列"""
        with self.file_lock:
            with open(self.file_path, 'w') as f:
                pass

    def get_message_count(self):
        """获取消息数量"""
        with self.file_lock:
            with open(self.file_path, 'r') as f:
                return len(f.readlines())

    def close(self):
        """关闭时的清理操作"""
        pass

@boost(BoosterParams(
    queue_name='test_txt_queue',
    broker_kind=BrokerEnum.EMPTY,  # 使用 EMPTY 表示完全自定义 broker
    concurrent_num=1,
    consumer_override_cls=TxtFileConsumer,
    publisher_override_cls=TxtFilePublisher,
    is_show_message_get_from_broker=True
))
def example_function(x):
    """示例函数"""
    print(f'开始处理 {x}')
    time.sleep(1)  # 模拟耗时操作
    print(f'完成处理 {x}')
    return x

if __name__ == '__main__':
    # 推送10个消息到队列
    for i in range(10):
        example_function.push(i)
    
    # 开始消费队列中的消息
    example_function.consume()
    ctrl_c_recv()
