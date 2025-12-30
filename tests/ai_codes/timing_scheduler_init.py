# -*- coding: utf-8 -*-
"""
Flask 应用启动时初始化 APScheduler 调度器
确保所有队列的 Redis JobStore 调度器都正确启动
"""

from funboost.core.active_cousumer_info_getter import QueuesConusmerParamsGetter, SingleQueueConusmerParamsGetter
from funboost.timing_job.timing_push import ApsJobAdder
from funboost import logger_getter

logger = logger_getter.get_logger('timing_jobs_init')

# 全局字典，存储已初始化的调度器
_initialized_schedulers = {}

def init_all_timing_schedulers():
    """
    初始化所有队列的定时任务调度器
    应该在 Flask 应用启动时调用一次
    """
    logger.info("开始初始化定时任务调度器...")
    
    all_queues = list(QueuesConusmerParamsGetter().get_all_queue_names())
    logger.info(f"发现 {len(all_queues)} 个队列")
    
    for queue_name in all_queues:
        try:
            # 为每个队列创建 Redis 模式的调度器
            booster = SingleQueueConusmerParamsGetter(queue_name)\
                .gen_booster_for_faas()
            
            # 创建并启动调度器
            job_adder = ApsJobAdder(booster, job_store_kind='redis', is_auto_start=True)
            
            # 检查是否有任务
            jobs = job_adder.aps_obj.get_jobs()
            
            _initialized_schedulers[queue_name] = job_adder.aps_obj
            
            logger.info(f"✓ 队列 '{queue_name}' 调度器已启动，当前任务数: {len(jobs)}")
            
        except Exception as e:
            logger.error(f"✗ 队列 '{queue_name}' 调度器初始化失败: {e}")
    
    logger.info(f"定时任务调度器初始化完成，共 {len(_initialized_schedulers)} 个调度器运行中")
    
    return _initialized_schedulers


def get_scheduler_for_queue(queue_name, job_store_kind='redis'):
    """
    获取指定队列的调度器
    如果不存在则创建
    """
    if job_store_kind == 'redis':
        key = queue_name
        if key not in _initialized_schedulers:
            try:
                booster = SingleQueueConusmerParamsGetter(queue_name)\
                    .gen_booster_for_faas()
                job_adder = ApsJobAdder(booster, job_store_kind='redis', is_auto_start=True)
                _initialized_schedulers[key] = job_adder.aps_obj
                logger.info(f"创建新的调度器: {queue_name}")
            except Exception as e:
                logger.error(f"创建调度器失败 {queue_name}: {e}")
                raise
        
        return _initialized_schedulers[key]
    else:
        # memory 模式使用全局调度器
        from funboost.timing_job.timing_job_base import funboost_aps_scheduler
        return funboost_aps_scheduler


# 在 app.py 中调用示例:
if __name__ == '__main__':
    # 测试初始化
    init_all_timing_schedulers()
    
    import time
    print("\\n调度器运行中，按 Ctrl+C 退出...")
    try:
        while True:
            time.sleep(60)
            # 定期检查调度器状态
            for queue_name, scheduler in _initialized_schedulers.items():
                jobs = scheduler.get_jobs()
                print(f"队列 {queue_name}: {len(jobs)} 个任务运行中")
    except KeyboardInterrupt:
        print("\\n停止调度器...")
