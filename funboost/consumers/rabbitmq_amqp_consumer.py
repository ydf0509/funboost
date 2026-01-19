# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2026/1/14
"""
使用 amqp 包实现的高性能 RabbitMQ Consumer。
amqp 是 Celery/Kombu 底层使用的 AMQP 客户端，性能比 pika 更好。

安装：pip install amqp (通常已随 celery/kombu 安装)
"""
import socket
import time
from funboost.consumers.base_consumer import AbstractConsumer


class RabbitmqAmqpConsumer(AbstractConsumer):
    """
    使用 amqp 包实现，高性能 AMQP 客户端。
    amqp 是 Celery/Kombu 底层依赖，性能比 pika 更好。
    """

    def _dispatch_task(self):
        def callback(message):
            """消息回调处理函数"""
            body = message.body
            if isinstance(body, bytes):
                body = body.decode('utf-8')
            kw = {'message': message, 'body': body, 'channel': rp.channel}
            self._submit_task(kw)

        # 复用 publisher 的连接和 channel
        rp = self.bulid_a_new_publisher_of_same_queue()
        rp.init_broker()

        # 设置 prefetch，控制消费者一次预取的消息数量
        rp.channel.basic_qos(
            prefetch_size=0,
            prefetch_count=self.consumer_params.concurrent_num * 2,
            a_global=False
        )

        # 开始消费
        no_ack = self.consumer_params.broker_exclusive_config['no_ack']
        rp.channel.basic_consume(
            queue=self.queue_name,
            callback=callback,
            no_ack=no_ack,
        )

        self._rp = rp

        self.logger.info(f'amqp 开始消费队列 {self.queue_name}')
        
        # 心跳间隔（秒），设置为比服务器心跳超时小的值
        heartbeat_interval = 5
        last_heartbeat_time = time.time()
        
        while True:
            try:
                # drain_events 使用较短超时，以便及时发送心跳
                rp.connection.drain_events(timeout=heartbeat_interval)
            except socket.timeout:
                # 超时是正常的，继续循环
                pass
            except OSError as e:
                # 连接被重置，尝试重连
                self.logger.error(f'amqp 连接异常: {type(e).__name__} {e}')
                self._reconnect(rp, callback, no_ack)
                last_heartbeat_time = time.time()
                continue
            except Exception as e:
                exc_name = type(e).__name__
                # 检查是否是连接相关异常 (需要重连)
                if ('Connection' in exc_name or 'Channel' in exc_name or 'AMQP' in exc_name or
                    'Recoverable' in exc_name):
                    self.logger.error(f'amqp 连接/通道异常: {exc_name} {e}，触发重连')
                    self._reconnect(rp, callback, no_ack)
                    last_heartbeat_time = time.time()
                    continue
                elif 'PreconditionFailed' in exc_name:
                    # PreconditionFailed 通常发生在 ack/reject 时，已在 _confirm_consume 中处理
                    self.logger.debug(f'amqp drain_events PreconditionFailed (已处理): {e}')
                else:
                    self.logger.error(f'amqp drain_events 异常: {exc_name} {e}')
            
            # 主动发送心跳
            try:
                current_time = time.time()
                if current_time - last_heartbeat_time >= heartbeat_interval:
                    # amqp 包的心跳检查
                    rp.connection.heartbeat_tick()
                    last_heartbeat_time = current_time
            except Exception as e:
                self.logger.warning(f'发送心跳失败: {e}')
    
    def _reconnect(self, rp, callback, no_ack):
        """重连逻辑"""
        try:
            time.sleep(5)
            rp.has_init_broker = 0  # 重置初始化标志
            rp.init_broker()
            rp.channel.basic_qos(
                prefetch_size=0,
                prefetch_count=self.consumer_params.concurrent_num,
                a_global=False
            )
            rp.channel.basic_consume(
                queue=self.queue_name,
                callback=callback,
                no_ack=no_ack,
            )
            self.logger.info('amqp 重连成功')
        except Exception as reconnect_error:
            self.logger.error(f'amqp 重连失败: {reconnect_error}')
            time.sleep(5)

    def _confirm_consume(self, kw):
        """确认消费"""
        if self.consumer_params.broker_exclusive_config['no_ack'] is False:
            try:
                # 使用当前有效的 channel 进行 ack (重连后 channel 会变化)
                self._rp.channel.basic_ack(kw['message'].delivery_tag)
            except Exception as e:
                exc_name = type(e).__name__
                # PreconditionFailed 表示 delivery tag 已失效（重连后导致），消息会被 RabbitMQ 自动重新投递
                if 'PreconditionFailed' in exc_name:
                    self.logger.debug(f'amqp ack 跳过（delivery tag 已失效，消息将重新投递）: {e}')
                else:
                    self.logger.error(f'amqp 确认消费失败 {exc_name} {e}')

    def _requeue(self, kw):
        """重新入队"""
        try:
            # 使用当前有效的 channel 进行 reject (重连后 channel 会变化)
            self._rp.channel.basic_reject(kw['message'].delivery_tag, requeue=True)
        except Exception as e:
            exc_name = type(e).__name__
            # PreconditionFailed 表示 delivery tag 已失效，消息会被 RabbitMQ 自动重新投递
            if 'PreconditionFailed' in exc_name:
                self.logger.debug(f'amqp requeue 跳过（delivery tag 已失效，消息将重新投递）: {e}')
            else:
                self.logger.error(f'amqp requeue 失败 {exc_name} {e}')
