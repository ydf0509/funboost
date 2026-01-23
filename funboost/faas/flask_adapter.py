"""
Flask 开箱即用，作者自带贡献，只需要用户的 app.register_blueprint(flask_blueprint)
即可自动给用户的Flask应用添加常用路由
包括发布消息， 根据task_id获取结果， 获取队列消息数量



使用说明:
    在用户自己的 Flask 项目中:
       app.register_blueprint(flask_blueprint)
    


"""

import traceback
from flask import Blueprint, request, jsonify

from funboost import AsyncResult, TaskOptions
from funboost.core.active_cousumer_info_getter import SingleQueueConusmerParamsGetter, QueuesConusmerParamsGetter, CareProjectNameEnv, ActiveCousumerProcessInfoGetter
from funboost.faas.faas_util import gen_aps_job_adder
from funboost.core.loggers import get_funboost_file_logger



logger = get_funboost_file_logger(__name__)

# 创建 Blueprint 实例，方便用户 register 到自己的 app 中
# 用户可以使用 app.register_blueprint(flask_blueprint)
flask_blueprint = Blueprint('funboost', __name__, url_prefix='/funboost')


@flask_blueprint.route("/publish", methods=['POST'])
def publish_msg():
    """
    发布消息接口
    
    请求体示例:
    {
        "queue_name": "test_queue",
        "msg_body": {"x": 1, "y": 2},
        "need_result": true,
        "timeout": 60
    }
    """
    status_and_result = None
    task_id = None
    
    try:
        # 获取 JSON 数据
        data = request.get_json()
        if not data:
            return jsonify({
                "succ": False,
                "msg": "请求体必须是 JSON 格式",
                "data": {
                    "task_id": None,
                    "status_and_result": None
                }
            }), 400
        
        queue_name = data.get('queue_name')
        msg_body = data.get('msg_body')
        need_result = data.get('need_result', False)
        timeout = data.get('timeout', 60)
        task_id_param = data.get('task_id')  # 可选：指定 task_id
        
        # 验证必填字段
        if not queue_name:
            return jsonify({
                "succ": False,
                "msg": "queue_name 字段必填",
                "data": {
                    "task_id": None,
                    "status_and_result": None
                }
            }), 400
        
        if not msg_body or not isinstance(msg_body, dict):
            return jsonify({
                "succ": False,
                "msg": "msg_body 字段必填且必须是字典类型",
                "data": {
                    "task_id": None,
                    "status_and_result": None
                }
            }), 400
        
        # BoostersManager.get_or_create_booster_by_queue_name 是通过queue_name反向得到或创建booster。
        # 不需要用户亲自判断queue_name，然后精确使用某个非常具体的消费函数，
        publisher = SingleQueueConusmerParamsGetter(queue_name).gen_publisher_for_faas()
        booster_params_by_redis = SingleQueueConusmerParamsGetter(queue_name).get_one_queue_params_use_cache()

        # 检查是否需要 RPC 模式
        if need_result:
            # 开启 RPC 模式发布（同步方式）
            async_result = publisher.publish(
                msg_body,
                task_id=task_id_param,  # 可选：指定 task_id（用于重试失败任务）
                task_options=TaskOptions(is_using_rpc_mode=True)
            )
            task_id = async_result.task_id
            
            # 等待结果（同步方式）
            print(async_result.task_id,timeout)
            status_and_result = AsyncResult(async_result.task_id, timeout=timeout).status_and_result
        else:
            # 普通发布（同步方式），可以指定 task_id
            async_result = publisher.publish(msg_body, task_id=task_id_param)
            task_id = async_result.task_id

        return jsonify({
            "succ": True,
            "msg": f'{queue_name} 队列,消息发布成功',
            "data": {
                "task_id": task_id,
                "status_and_result": status_and_result
            }
        })
        
    except Exception as e:
        return jsonify({
            "succ": False,
            "msg": f'消息发布失败 {type(e)} {e} {traceback.format_exc()}',
            "data": {
                "task_id": task_id,
                "status_and_result": status_and_result
            }
        }), 500


@flask_blueprint.route("/get_result", methods=['GET'])
def get_result():
    """
    根据 task_id 获取任务执行结果
    
    查询参数:
        task_id: str - 任务ID（必填）
        timeout: int - 超时时间，默认5秒
    """
    try:
        task_id = request.args.get('task_id')
        timeout = int(request.args.get('timeout', 5))
        
        if not task_id:
            return jsonify({
                "succ": False,
                "msg": "task_id 参数必填",
                "data": {
                    "task_id": None,
                    "status_and_result": None
                }
            }), 400
        
        # 尝试获取结果，默认给个短的 timeout 防止一直阻塞
        # 注意：如果任务还在运行，AsyncResult 会阻塞直到 timeout
        # 如果任务早已完成并过期，这里可能返回 None
        status_and_result = AsyncResult(task_id, timeout=timeout).status_and_result
        
        if status_and_result is not None:
            return jsonify({
                "succ": True,
                "msg": "获取成功",
                "data": {
                    "task_id": task_id,
                    "status_and_result": status_and_result
                }
            })
        else:
            return jsonify({
                "succ": False,
                "msg": "未获取到结果(可能已过期或未开始执行或超时)",
                "data": {
                    "task_id": task_id,
                    "status_and_result": None
                }
            })
            
    except Exception as e:
        return jsonify({
            "succ": False,
            "msg": f"获取结果出错: {str(e)}",
            "data": {
                "task_id": task_id if 'task_id' in locals() else None,
                "status_and_result": None
            }
        }), 500


@flask_blueprint.route("/get_msg_count", methods=['GET'])
def get_msg_count():
    """
    根据 queue_name 获取消息数量
    
    查询参数:
        queue_name: str - 队列名称（必填）
    """
    try:
        queue_name = request.args.get('queue_name')
        
        if not queue_name:
            return jsonify({
                "succ": False,
                "msg": "queue_name 参数必填",
                "data": {
                    "queue_name": None,
                    "count": -1
                }
            },), 400
        

        publisher = SingleQueueConusmerParamsGetter(queue_name).gen_publisher_for_faas()
        # 获取消息数量（注意：某些中间件可能不支持准确计数，返回-1）
        count = publisher.get_message_count()
        
        return jsonify({
            "succ": True,
            "msg": "获取成功",
            "data": {
                "queue_name": queue_name,
                "count": count
            }
        })
        
    except Exception as e:
        return jsonify({
            "succ": False,
            "msg": f"获取消息数量失败: {str(e)}",
            "data": {
                "queue_name": queue_name if 'queue_name' in locals() else None,
                "count": -1
            }
        }), 500


@flask_blueprint.route("/get_all_queues", methods=['GET'])
def get_all_queues():
    """
    获取所有已注册的队列名称
    
    返回所有通过 @boost 装饰器注册的队列名称列表
    """
    try:
        # 获取所有队列名称
        all_queues = QueuesConusmerParamsGetter().get_all_queue_names()
        
        return jsonify({
            "succ": True,
            "msg": "获取成功",
            "data": {
                "queues": all_queues,
                "count": len(all_queues)
            }
        })
        
    except Exception as e:
        return jsonify({
            "succ": False,
            "msg": f"获取所有队列失败: {str(e)}",
            "data": {
                "queues": [],
                "count": 0
            }
        }), 500




@flask_blueprint.route("/clear_queue", methods=['POST'])
def clear_queue():
    """
    清空队列中的所有消息
    
    请求体 (JSON):
        {
            "queue_name": "队列名称"
        }
    
    返回:
        清空操作的结果
        
    说明:
        此接口会清空指定队列中的所有待消费消息。
        ⚠️ 此操作不可逆，请谨慎使用！
        
    注意:
        broker_kind 会自动从已注册的 booster 中获取，无需手动指定。
    """
    try:
        data = request.get_json()
        queue_name = data.get('queue_name')
        
        if not queue_name:
            return jsonify({
                "succ": False,
                "msg": "queue_name 字段必填",
                "data": None
            }), 400
        
        # 通过 queue_name 自动获取对应的 publisher
        publisher = SingleQueueConusmerParamsGetter(queue_name).gen_publisher_for_faas()
        publisher.clear()
        
        return jsonify({
            "succ": True,
            "msg": f"队列 {queue_name} 清空成功",
            "data": {
                "queue_name": queue_name,
                "success": True
            }
        })
        
    except Exception as e:
        logger.exception(f'清空队列失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"清空队列 {queue_name if 'queue_name' in locals() else ''} 失败: {str(e)}",
            "data": {
                "queue_name": queue_name if 'queue_name' in locals() else None,
                "success": False
            }
        }), 500



# ==================== 定时任务管理接口 ====================



@flask_blueprint.route("/get_one_queue_config", methods=['GET'])
def get_one_queue_config():
    """
    获取单个队列的配置信息
    
    查询参数:
        queue_name: 队列名称（必填）
    
    返回:
        队列的配置信息，包括函数入参信息 (final_func_input_params_info)
    """
    try:
        queue_name = request.args.get('queue_name')
        
        if not queue_name:
            return jsonify({
                "succ": False,
                "msg": "queue_name 参数必填",
                "data": None
            }), 400
        
        queue_params = SingleQueueConusmerParamsGetter(queue_name).get_one_queue_params()
        
        return jsonify({
            "succ": True,
            "msg": "获取成功",
            "data": queue_params
        })
        
    except Exception as e:
        logger.exception(f'获取队列配置失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"获取队列配置失败: {str(e)}",
            "data": None
        }), 500


@flask_blueprint.route("/get_queues_config", methods=['GET'])
def get_queues_config():
    """
    获取所有队列的配置信息
    
    返回所有已注册队列的详细配置参数，包括：
    - 队列名称
    - broker 类型
    - 并发数量
    - QPS 限制
    - 是否启用 RPC 模式
    - ！！！重要，消费函数的入参名字列表在 auto_generate_info.final_func_input_params_info 中
    - 等等其他 @boost 装饰器的所有参数
    
    主要用于前端可视化展示和管理
    """
    try:
        queues_config = QueuesConusmerParamsGetter().get_queues_params()
        
        return jsonify({
            "succ": True,
            "msg": "获取成功",
            "data": {
                "queues_config": queues_config,
                "count": len(queues_config)
            }
        })
    except Exception as e:
        logger.exception(f'获取队列配置失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"获取队列配置失败: {str(e)}",
            "data": {
                "queues_config": {},
                "count": 0
            }
        }), 500


@flask_blueprint.route("/get_queue_run_info", methods=['GET'])
def get_queue_run_info():
    """
    获取单个队列的运行信息
    
    查询参数:
        queue_name: 队列名称（必填）
    
    返回:
        队列的详细运行信息，包括：
        - queue_params: 队列配置参数
        - active_consumers: 活跃的消费者列表
        - pause_flag: 暂停标志（-1,0表示未暂停，1表示已暂停）
        - msg_num_in_broker: broker中的消息数量（实时）
        - history_run_count: 历史运行总次数
        - history_run_fail_count: 历史失败总次数
        - all_consumers_last_x_s_execute_count: 所有消费进程，最近X秒所有消费者的执行次数
        - all_consumers_last_x_s_execute_count_fail: 所有消费进程，最近X秒所有消费者的失败次数
        - all_consumers_last_x_s_avarage_function_spend_time: 所有消费进程，最近X秒的平均函数耗时
        - all_consumers_avarage_function_spend_time_from_start: 所有消费进程，从启动开始的平均函数耗时
        - all_consumers_total_consume_count_from_start: 所有消费进程，从启动开始的总消费次数
        - all_consumers_total_consume_count_from_start_fail: 所有消费进程，从启动开始的总失败次数
        - all_consumers_last_execute_task_time: 所有消费进程中，最后一次执行任务的时间戳
    """
    try:
        queue_name = request.args.get('queue_name')
        
        if not queue_name:
            return jsonify({
                "succ": False,
                "msg": "queue_name 参数必填",
                "data": None
            }), 400
        
        # 获取单个队列的运行信息
        queue_info = SingleQueueConusmerParamsGetter(queue_name).get_one_queue_params_and_active_consumers()
        
        return jsonify({
            "succ": True,
            "msg": "获取成功",
            "data": queue_info
        })
        
    except Exception as e:
        logger.exception(f'获取队列运行信息失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"获取队列运行信息失败: {str(e)}",
            "data": None
        }), 500


@flask_blueprint.route("/add_timing_job", methods=['POST'])
def add_timing_job():
    """
    添加定时任务
    
    支持三种触发方式:
    1. date: 在指定日期时间执行一次
       - 需要提供: run_date
       - 示例: {"trigger": "date", "run_date": "2025-12-03 15:00:00"}
    
    2. interval: 按固定时间间隔执行
       - 需要提供: weeks, days, hours, minutes, seconds 中的至少一个
       - 示例: {"trigger": "interval", "seconds": 10}
    
    3. cron: 按cron表达式执行
       - 需要提供: year, month, day, week, day_of_week, hour, minute, second 中的至少一个
       - 示例: {"trigger": "cron", "hour": "*/2", "minute": "30"}
    
    请求体示例:
    {
        "queue_name": "test_queue",
        "trigger": "interval",
        "seconds": 10,
        "job_id": "my_job_001",
        "job_store_kind": "redis",
        "replace_existing": false
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "succ": False,
                "msg": "请求体必须是 JSON 格式",
                "data": None
            }), 400
        
        queue_name = data.get('queue_name')
        trigger = data.get('trigger')
        job_id = data.get('job_id')
        job_store_kind = data.get('job_store_kind', 'redis')
        replace_existing = data.get('replace_existing', False)
        
        if not queue_name:
            return jsonify({
                "succ": False,
                "msg": "queue_name 字段必填",
                "data": None
            }), 400
        
        if not trigger or trigger not in ['date', 'interval', 'cron']:
            return jsonify({
                "succ": False,
                "msg": "trigger 字段必填，且必须是 'date', 'interval', 'cron' 之一",
                "data": None
            }), 400
        
        # 获取 booster
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)

        # print(888888,job_adder.aps_obj,id(job_adder.aps_obj),job_adder.aps_obj.get_jobs())

        # 构建触发器参数
        trigger_args = {}
        
        if trigger == 'date':
            if data.get('run_date'):
                trigger_args['run_date'] = data.get('run_date')
        
        elif trigger == 'interval':
            if data.get('weeks') is not None:
                trigger_args['weeks'] = data.get('weeks')
            if data.get('days') is not None:
                trigger_args['days'] = data.get('days')
            if data.get('hours') is not None:
                trigger_args['hours'] = data.get('hours')
            if data.get('minutes') is not None:
                trigger_args['minutes'] = data.get('minutes')
            if data.get('seconds') is not None:
                trigger_args['seconds'] = data.get('seconds')
        
        elif trigger == 'cron':
            if data.get('year') is not None:
                trigger_args['year'] = data.get('year')
            if data.get('month') is not None:
                trigger_args['month'] = data.get('month')
            if data.get('day') is not None:
                trigger_args['day'] = data.get('day')
            if data.get('week') is not None:
                trigger_args['week'] = data.get('week')
            if data.get('day_of_week') is not None:
                trigger_args['day_of_week'] = data.get('day_of_week')
            if data.get('hour') is not None:
                trigger_args['hour'] = data.get('hour')
            if data.get('minute') is not None:
                trigger_args['minute'] = data.get('minute')
            if data.get('second') is not None:
                trigger_args['second'] = data.get('second')
        
        # 添加任务
        job = job_adder.add_push_job(
            trigger=trigger,
            args=data.get('args'),
            kwargs=data.get('kwargs'),
            id=job_id,
            replace_existing=replace_existing,
            **trigger_args
        )
        
        return jsonify({
            "succ": True,
            "msg": "定时任务添加成功",
            "data": {
                "job_id": job.id,
                "queue_name": queue_name,
                "trigger": str(job.trigger),
                "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                "status": "running",
                "kwargs": data.get('kwargs')
            }
        })
        
    except Exception as e:
        logger.exception(f'添加定时任务失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"添加定时任务失败: {str(e)}\n{traceback.format_exc()}",
            "data": None
        }), 500


@flask_blueprint.route("/get_timing_jobs", methods=['GET'])
def get_timing_jobs():
    """
    获取定时任务列表
    
    查询参数:
        queue_name: 队列名称（可选，如果不提供则获取所有队列的任务）
        job_store_kind: 任务存储方式，'redis' 或 'memory'，默认 'redis'
    
    返回格式:
        {
            "succ": True,
            "msg": "获取成功",
            "data": {
                "jobs_by_queue": {
                    "queue_name1": [job1, job2, ...],
                    "queue_name2": [job3, ...],
                    ...
                },
                "total_count": 总任务数
            }
        }
    """
    try:
        queue_name = request.args.get('queue_name')
        job_store_kind = request.args.get('job_store_kind', 'redis')
        
        # 使用字典格式存储：{queue_name: [jobs]}
        jobs_by_queue = {}
        total_count = 0
        
        if queue_name:
            # 获取指定队列的任务
            jobs_by_queue[queue_name] = []
            try:
                job_adder = gen_aps_job_adder(queue_name, job_store_kind)
                jobs = job_adder.aps_obj.get_jobs()
                
                for job in jobs:
                    # 判断任务状态：next_run_time 为 None 表示任务已暂停
                    status = "paused" if job.next_run_time is None else "running"
                    # 获取任务的 kwargs 参数
                    kwargs = job.kwargs if hasattr(job, 'kwargs') and job.kwargs else {}
                    jobs_by_queue[queue_name].append({
                        "job_id": job.id,
                        "queue_name": queue_name,
                        "trigger": str(job.trigger),
                        "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                        "status": status,
                        "kwargs": kwargs
                    })
                    total_count += 1
            except Exception as e:
                logger.exception(f'获取定时任务列表失败: {str(e)}')
               
        else:
            # 获取所有队列的任务
            all_queues = list(QueuesConusmerParamsGetter().get_all_queue_names())
            for q_name in all_queues:
                jobs_by_queue[q_name] = []  # 初始化为空数组
                try:
                    job_adder = gen_aps_job_adder(q_name, job_store_kind)
                    jobs = job_adder.aps_obj.get_jobs()
                    
                    for job in jobs:
                        # 判断任务状态：next_run_time 为 None 表示任务已暂停
                        status = "paused" if job.next_run_time is None else "running"
                        # 获取任务的 kwargs 参数
                        kwargs = job.kwargs if hasattr(job, 'kwargs') and job.kwargs else {}
                        jobs_by_queue[q_name].append({
                            "job_id": job.id,
                            "queue_name": q_name,
                            "trigger": str(job.trigger),
                            "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                            "status": status,
                            "kwargs": kwargs
                        })
                        total_count += 1
                except Exception as e:
                    logger.exception(f'获取定时任务列表失败: {str(e)}')
                 
        
        return jsonify({
            "succ": True,
            "msg": "获取成功",
            "data": {
                "jobs_by_queue": jobs_by_queue,
                "total_count": total_count
            }
        })
        
    except Exception as e:
        logger.exception(f'获取定时任务列表失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"获取定时任务列表失败: {str(e)}",
            "data": {
                "jobs_by_queue": {},
                "total_count": 0
            }
        }), 500


@flask_blueprint.route("/get_timing_job", methods=['GET'])
def get_timing_job():
    """
    获取单个定时任务的详细信息
    
    查询参数:
        job_id: 任务ID（必填）
        queue_name: 队列名称（必填）
        job_store_kind: 任务存储方式，'redis' 或 'memory'，默认 'redis'
    """
    try:
        job_id = request.args.get('job_id')
        queue_name = request.args.get('queue_name')
        job_store_kind = request.args.get('job_store_kind', 'redis')
        
        if not job_id or not queue_name:
            return jsonify({
                "succ": False,
                "msg": "job_id 和 queue_name 参数必填",
                "data": None
            }), 400
        
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        
        # 获取指定的任务
        job = job_adder.aps_obj.get_job(job_id)
        
        if job:
            status = "paused" if job.next_run_time is None else "running"
            kwargs = job.kwargs if hasattr(job, 'kwargs') and job.kwargs else {}
            return jsonify({
                "succ": True,
                "msg": "获取成功",
                "data": {
                    "job_id": job.id,
                    "queue_name": queue_name,
                    "trigger": str(job.trigger),
                    "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                    "status": status,
                    "kwargs": kwargs
                }
            })
        else:
            return jsonify({
                "succ": False,
                "msg": f"任务 {job_id} 不存在",
                "data": None
            }), 404
        
    except Exception as e:
        logger.exception(f'获取定时任务失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"获取定时任务失败: {str(e)}",
            "data": None
        }), 500


@flask_blueprint.route("/delete_timing_job", methods=['DELETE'])
def delete_timing_job():
    """
    删除定时任务
    
    查询参数:
        job_id: 任务ID（必填）
        queue_name: 队列名称（必填）
        job_store_kind: 任务存储方式，'redis' 或 'memory'，默认 'redis'
    """
    try:
        job_id = request.args.get('job_id')
        queue_name = request.args.get('queue_name')
        job_store_kind = request.args.get('job_store_kind', 'redis')
        
        if not job_id or not queue_name:
            return jsonify({
                "succ": False,
                "msg": "job_id 和 queue_name 参数必填",
                "data": None
            }), 400
        
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        job_adder.aps_obj.remove_job(job_id)
        
        return jsonify({
            "succ": True,
            "msg": f"定时任务 {job_id} 删除成功",
            "data": None
        })
        
    except Exception as e:
        logger.exception(f'删除定时任务失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"删除定时任务失败: {str(e)}",
            "data": None
        }), 500


@flask_blueprint.route("/delete_all_timing_jobs", methods=['DELETE'])
def delete_all_timing_jobs():
    """
    删除所有定时任务
    
    查询参数:
        queue_name: 队列名称（可选，如果不提供则删除所有队列的所有任务）
        job_store_kind: 任务存储方式，'redis' 或 'memory'，默认 'redis'
    """
    try:
        queue_name = request.args.get('queue_name')
        job_store_kind = request.args.get('job_store_kind', 'redis')
        
        deleted_count = 0
        failed_jobs = []
        
        if queue_name:
            # 删除指定队列的所有任务
            try:
                job_adder = gen_aps_job_adder(queue_name, job_store_kind)
                jobs = job_adder.aps_obj.get_jobs()
                
                for job in jobs:
                    try:
                        job_adder.aps_obj.remove_job(job.id)
                        deleted_count += 1
                    except Exception as e:
                        failed_jobs.append(f"{job.id}: {str(e)}")
            except Exception as e:
                return jsonify({
                    "succ": False,
                    "msg": f"删除队列 {queue_name} 的任务失败: {str(e)}",
                    "data": {
                        "deleted_count": deleted_count,
                        "failed_jobs": failed_jobs
                    }
                }), 500
        else:
            # 删除所有队列的所有任务
            all_queues = list(QueuesConusmerParamsGetter().get_all_queue_names())
            for q_name in all_queues:
                try:
                    job_adder = gen_aps_job_adder(q_name, job_store_kind)
                    jobs = job_adder.aps_obj.get_jobs()
                    
                    for job in jobs:
                        try:
                            job_adder.aps_obj.remove_job(job.id)
                            deleted_count += 1
                        except Exception as e:
                            failed_jobs.append(f"{q_name}/{job.id}: {str(e)}")
                except Exception as e:
                    logger.exception(f'删除队列 {q_name} 的任务失败: {str(e)}')
                    # 队列没有任务或出错，继续处理下一个队列
                    
        
        return jsonify({
            "succ": True,
            "msg": f"成功删除 {deleted_count} 个定时任务",
            "data": {
                "deleted_count": deleted_count,
                "failed_jobs": failed_jobs
            }
        })
        
    except Exception as e:
        logger.exception(f'删除所有定时任务失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"删除所有定时任务失败: {str(e)}",
            "data": {
                "deleted_count": 0,
                "failed_jobs": []
            }
        }), 500


@flask_blueprint.route("/pause_timing_job", methods=['POST'])
def pause_timing_job():
    """
    暂停定时任务
    
    查询参数:
        job_id: 任务ID（必填）
        queue_name: 队列名称（必填）
        job_store_kind: 任务存储方式，'redis' 或 'memory'，默认 'redis'
    """
    try:
        job_id = request.args.get('job_id')
        queue_name = request.args.get('queue_name')
        job_store_kind = request.args.get('job_store_kind', 'redis')
        
        if not job_id or not queue_name:
            return jsonify({
                "succ": False,
                "msg": "job_id 和 queue_name 参数必填",
                "data": None
            }), 400
        
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        job_adder.aps_obj.pause_job(job_id)
        
        return jsonify({
            "succ": True,
            "msg": f"定时任务 {job_id} 已暂停",
            "data": None
        })
        
    except Exception as e:
        logger.exception(f'暂停定时任务失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"暂停定时任务失败: {str(e)}",
            "data": None
        }), 500


@flask_blueprint.route("/resume_timing_job", methods=['POST'])
def resume_timing_job():
    """
    恢复定时任务
    
    查询参数:
        job_id: 任务ID（必填）
        queue_name: 队列名称（必填）
        job_store_kind: 任务存储方式，'redis' 或 'memory'，默认 'redis'
    """
    try:
        job_id = request.args.get('job_id')
        queue_name = request.args.get('queue_name')
        job_store_kind = request.args.get('job_store_kind', 'redis')
        
        if not job_id or not queue_name:
            return jsonify({
                "succ": False,
                "msg": "job_id 和 queue_name 参数必填",
                "data": None
            }), 400
        
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        job_adder.aps_obj.resume_job(job_id)
        
        return jsonify({
            "succ": True,
            "msg": f"定时任务 {job_id} 已恢复",
            "data": None
        })
        
    except Exception as e:
        logger.exception(f'恢复定时任务失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"恢复定时任务失败: {str(e)}",
            "data": None
        }), 500

















@flask_blueprint.route("/get_scheduler_status", methods=['GET'])
def get_scheduler_status():
    """
    获取定时器调度器状态
    
    查询参数:
        queue_name: 队列名称（必填）
        job_store_kind: 任务存储方式，'redis' 或 'memory'，默认 'redis'
        
    返回:
        status: 0(已停止), 1(运行中), 2(已暂停)
    """
    try:
        queue_name = request.args.get('queue_name')
        job_store_kind = request.args.get('job_store_kind', 'redis')
        
        if not queue_name:
            return jsonify({
                "succ": False,
                "msg": "queue_name 参数必填",
                "data": None
            }), 400
            
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        
        state_map = {0: 'stopped', 1: 'running', 2: 'paused'}
        state = job_adder.aps_obj.state
        
        return jsonify({
            "succ": True,
            "msg": "获取成功",
            "data": {
                "queue_name": queue_name,
                "status_code": state,
                "status_str": state_map.get(state, 'unknown')
            }
        })
        
    except Exception as e:
        logger.exception(f'获取调度器状态失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"获取调度器状态失败: {str(e)}",
            "data": None
        }), 500


@flask_blueprint.route("/pause_scheduler", methods=['POST'])
def pause_scheduler():
    """
    暂停定时器调度器
    注意：这只会暂停当前进程中的调度器实例。如果部署了多实例，可能需要单独控制。
    
    查询参数:
        queue_name: 队列名称（必填）
        job_store_kind: 任务存储方式，'redis' 或 'memory'，默认 'redis'
    """
    try:
        queue_name = request.args.get('queue_name')
        job_store_kind = request.args.get('job_store_kind', 'redis')
        
        if not queue_name:
            return jsonify({
                "succ": False,
                "msg": "queue_name 参数必填",
                "data": None
            }), 400
            
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        job_adder.aps_obj.pause()
        
        return jsonify({
            "succ": True,
            "msg": f"调度器已暂停 ({queue_name})",
            "data": {
                "queue_name": queue_name,
                "status_str": "paused"
            }
        })
        
    except Exception as e:
        logger.exception(f'暂停调度器失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"暂停调度器失败: {str(e)}",
            "data": None
        }), 500


@flask_blueprint.route("/resume_scheduler", methods=['POST'])
def resume_scheduler():
    """
    恢复运行定时器调度器
    
    查询参数:
        queue_name: 队列名称（必填）
        job_store_kind: 任务存储方式，'redis' 或 'memory'，默认 'redis'
    """
    try:
        queue_name = request.args.get('queue_name')
        job_store_kind = request.args.get('job_store_kind', 'redis')
        
        if not queue_name:
            return jsonify({
                "succ": False,
                "msg": "queue_name 参数必填",
                "data": None
            }), 400
            
        job_adder = gen_aps_job_adder(queue_name, job_store_kind)
        job_adder.aps_obj.resume()
        
        return jsonify({
            "succ": True,
            "msg": f"调度器已恢复运行 ({queue_name})",
            "data": {
                "queue_name": queue_name,
                "status_str": "running"
            }
        })
        
    except Exception as e:
        logger.exception(f'恢复调度器失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"恢复调度器失败: {str(e)}",
            "data": None
        }), 500


@flask_blueprint.route("/deprecate_queue", methods=['DELETE'])
def deprecate_queue():
    """
    废弃队列 - 从 Redis 的 funboost_all_queue_names set 和 项目的队列名下 移除队列名
    
    请求体 (JSON):
        {
            "queue_name": "要废弃的队列名称"
        }
    
    返回:
        {
            "succ": True/False,
            "msg": "提示信息",
            "data": {
                "queue_name": "队列名称",
                "removed": True/False
            }
        }
    """
    try:
        data = request.get_json()
        queue_name = data.get('queue_name')
        
        if not queue_name:
            return jsonify({
                "succ": False,
                "msg": "缺少参数 queue_name",
                "data": None
            }), 400
        
        # 调用 SingleQueueConusmerParamsGetter 的 deprecate_queue 方法
        SingleQueueConusmerParamsGetter(queue_name).deprecate_queue()
        
        logger.info(f'成功废弃队列: {queue_name}')
        return jsonify({
            "succ": True,
            "msg": f"成功废弃队列: {queue_name}",
            "data": {
                "queue_name": queue_name,
                "removed": True
            }
        })
        
    except Exception as e:
        logger.exception(f'废弃队列失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"废弃队列失败: {str(e)}",
            "data": None
        }), 500


# ==================== care_project_name 项目筛选接口 ====================

@flask_blueprint.route("/get_care_project_name", methods=['GET'])
def get_care_project_name():
    """
    获取当前的 care_project_name 设置
    
    返回:
        {
            "succ": True,
            "msg": "获取成功",
            "data": {
                "care_project_name": "项目名称或None"
            }
        }
    """
    try:
        care_project_name = CareProjectNameEnv.get()
        
        return jsonify({
            "succ": True,
            "msg": "获取成功",
            "data": {
                "care_project_name": care_project_name
            }
        })
        
    except Exception as e:
        logger.exception(f'获取 care_project_name 失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"获取失败: {str(e)}",
            "data": None
        }), 500


@flask_blueprint.route("/set_care_project_name", methods=['POST'])
def set_care_project_name():
    """
    设置 care_project_name
    
    请求体 (JSON):
        {
            "care_project_name": "项目名称" 或 "" (空字符串表示不限制)
        }
    
    返回:
        {
            "succ": True,
            "msg": "设置成功",
            "data": {
                "care_project_name": "设置后的值"
            }
        }
    """
    try:
        data = request.get_json()
        care_project_name = data.get('care_project_name', '')
        
        # 空字符串表示清除限制，设置为空字符串（环境变量中）
        CareProjectNameEnv.set(care_project_name)
        
        # 如果设置为空字符串，返回时显示为 None
        display_value = care_project_name if care_project_name else None
        
        logger.info(f'设置 care_project_name 为: {display_value}')
        return jsonify({
            "succ": True,
            "msg": f"设置成功: {display_value if display_value else '不限制（显示全部）'}",
            "data": {
                "care_project_name": display_value
            }
        })
        
    except Exception as e:
        logger.exception(f'设置 care_project_name 失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"设置失败: {str(e)}",
            "data": None
        }), 500


@flask_blueprint.route("/get_all_project_names", methods=['GET'])
def get_all_project_names():
    """
    获取所有已注册的项目名称列表
    
    返回:
        {
            "succ": True,
            "msg": "获取成功",
            "data": {
                "project_names": ["project1", "project2", ...],
                "count": 数量
            }
        }
    """
    try:
        # 使用 QueuesConusmerParamsGetter 获取所有项目名称
        project_names = QueuesConusmerParamsGetter().get_all_project_names()
        
        return jsonify({
            "succ": True,
            "msg": "获取成功",
            "data": {
                "project_names": sorted(project_names) if project_names else [],
                "count": len(project_names) if project_names else 0
            }
        })
        
    except Exception as e:
        logger.exception(f'获取项目名称列表失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"获取项目名称列表失败: {str(e)}",
            "data": {
                "project_names": [],
                "count": 0
            }
        }), 500


# ==================== 运行中消费者信息接口 ====================

@flask_blueprint.route("/running_consumer/hearbeat_info_by_queue_name", methods=['GET'])
def hearbeat_info_by_queue_name():
    """
    按队列名获取消费者心跳信息
    
    查询参数:
        queue_name: 队列名称（可选，不传或传"所有"则返回所有消费者）
    
    返回:
        消费者心跳信息列表
    """
    try:
        queue_name = request.args.get("queue_name")
        if queue_name in ("所有", None, ""):
            info_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_queue_name()
            ret_list = []
            for q_name, dic in info_map.items():
                ret_list.extend(dic)
            return jsonify({
                "succ": True,
                "msg": "获取成功",
                "data": ret_list
            })
        else:
            data = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_queue_name(queue_name)
            return jsonify({
                "succ": True,
                "msg": "获取成功",
                "data": data
            })
    except Exception as e:
        logger.exception(f'获取消费者心跳信息失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"获取消费者心跳信息失败: {str(e)}",
            "data": []
        }), 500


@flask_blueprint.route("/running_consumer/hearbeat_info_by_ip", methods=['GET'])
def hearbeat_info_by_ip():
    """
    按 IP 获取消费者心跳信息
    
    查询参数:
        ip: IP 地址（可选，不传或传"所有"则返回所有消费者）
    
    返回:
        消费者心跳信息列表
    """
    try:
        ip = request.args.get("ip")
        if ip in ("所有", None, ""):
            info_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_ip()
            ret_list = []
            for q_name, dic in info_map.items():
                ret_list.extend(dic)
            return jsonify({
                "succ": True,
                "msg": "获取成功",
                "data": ret_list
            })
        else:
            data = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_ip(ip)
            return jsonify({
                "succ": True,
                "msg": "获取成功",
                "data": data
            })
    except Exception as e:
        logger.exception(f'获取消费者心跳信息失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"获取消费者心跳信息失败: {str(e)}",
            "data": []
        }), 500


@flask_blueprint.route("/running_consumer/hearbeat_info_partion_by_queue_name", methods=['GET'])
def hearbeat_info_partion_by_queue_name():
    """
    按队列名分组统计消费者数量
    
    返回:
        队列名列表及每个队列的消费者数量，第一项为"所有"表示总数
    """
    try:
        info_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_queue_name()
        ret_list = []
        total_count = 0
        for k, v in info_map.items():
            ret_list.append({"collection_name": k, "count": len(v)})
            total_count += len(v)
        ret_list = sorted(ret_list, key=lambda x: x["collection_name"])
        ret_list.insert(0, {"collection_name": "所有", "count": total_count})
        return jsonify({
            "succ": True,
            "msg": "获取成功",
            "data": ret_list
        })
    except Exception as e:
        logger.exception(f'获取消费者分组统计失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"获取消费者分组统计失败: {str(e)}",
            "data": []
        }), 500


@flask_blueprint.route("/running_consumer/hearbeat_info_partion_by_ip", methods=['GET'])
def hearbeat_info_partion_by_ip():
    """
    按 IP 分组统计消费者数量
    
    返回:
        IP 列表及每个 IP 的消费者数量，第一项为"所有"表示总数
    """
    try:
        info_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_ip()
        ret_list = []
        total_count = 0
        for k, v in info_map.items():
            ret_list.append({"collection_name": k, "count": len(v)})
            total_count += len(v)
        ret_list = sorted(ret_list, key=lambda x: x["collection_name"])
        ret_list.insert(0, {"collection_name": "所有", "count": total_count})
        return jsonify({
            "succ": True,
            "msg": "获取成功",
            "data": ret_list
        })
    except Exception as e:
        logger.exception(f'获取消费者分组统计失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"获取消费者分组统计失败: {str(e)}",
            "data": []
        }), 500


@flask_blueprint.route("/queues_params_and_active_consumers", methods=['GET'])
def get_queues_params_and_active_consumers():
    """
    获取所有队列的参数配置和活跃消费者信息
    
    返回:
        所有队列的配置参数及其活跃消费者列表
    """
    try:
        data = QueuesConusmerParamsGetter().get_queues_params_and_active_consumers()
        return jsonify({
            "succ": True,
            "msg": "获取成功",
            "data": data
        })
    except Exception as e:
        logger.exception(f'获取队列参数和活跃消费者失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"获取队列参数和活跃消费者失败: {str(e)}",
            "data": {}
        }), 500


@flask_blueprint.route("/get_msg_num_all_queues", methods=['GET'])
def get_msg_num_all_queues():
    """
    批量获取所有队列的消息数量
    
    说明:
        这个是通过消费者周期每隔10秒上报到redis的，性能好。
        不需要实时获取每个消息队列，直接从redis读取所有队列的消息数量。
    
    返回:
        {queue_name: msg_count, ...}
    """
    try:
        data = QueuesConusmerParamsGetter().get_msg_num(ignore_report_ts=True)
        return jsonify({
            "succ": True,
            "msg": "获取成功",
            "data": data
        })
    except Exception as e:
        logger.exception(f'获取所有队列消息数量失败: {str(e)}')
        return jsonify({
            "succ": False,
            "msg": f"获取所有队列消息数量失败: {str(e)}",
            "data": {}
        }), 500


# 运行应用 (仅在作为主脚本运行时创建 app)
if __name__ == "__main__":
    from flask import Flask


    # 这是一个示例，展示用户如何将 flask_blueprint 集成到自己的 app 中
    app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False
    app.register_blueprint(flask_blueprint)

    @app.route('/')
    def index():
        return "Funboost Flask API 服务运行中！"

    print("启动 Funboost Flask API 服务...")
    print("访问地址: http://127.0.0.1:5000")

    app.run(host="0.0.0.0", port=5000, debug=True)
