# web_app.py
from flask import Flask, request, jsonify
from funboost import ApsJobAdder
from tasks import dynamic_task  # 导入任务函数，以便 ApsJobAdder 知道要调度谁

app = Flask(__name__)

# 创建一个 ApsJobAdder 实例。
# 关键点：job_store_kind='redis'，这样定时计划会保存在 Redis 中，
# 使得 Web 端和后台 Worker 端可以共享这些计划。

# 启动调度器但使其处于暂停状态。
# 这会激活与后端作业存储(Redis)的连接，使得 get_jobs/add_job/remove_job 等管理功能可以正常工作，
# 但它不会实际触发任何定时任务的执行。
job_adder = ApsJobAdder(dynamic_task, job_store_kind='redis', is_auto_paused=True,is_auto_start=True)



@app.route('/add_task', methods=['POST'])
def add_task():
    """添加一个新的周期性定时任务"""
    data = request.json
    task_id = data.get('task_id')
    interval_seconds = data.get('interval_seconds', 10)
    message = data.get('message', '默认消息')

    if not task_id:
        return jsonify({"error": "task_id is required"}), 400

    try:
        job_adder.add_push_job(
            trigger='interval',
            seconds=int(interval_seconds),
            id=str(task_id),
            replace_existing=True,
            kwargs={'task_id': task_id, 'message': message}
        )
        return jsonify({
            "status": "success",
            "message": f"任务 '{task_id}' 已添加，每 {interval_seconds} 秒执行一次。"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get_tasks', methods=['GET'])
def get_tasks():
    """获取所有已安排的定时任务"""
    try:
        jobs = job_adder.aps_obj.get_jobs()
        job_list = [{
            "id": job.id,
            "next_run_time": str(job.next_run_time),
            "trigger": str(job.trigger)
        } for job in jobs]
        return jsonify(job_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/remove_task/<string:task_id>', methods=['DELETE'])
def remove_task(task_id: str):
    """删除一个指定的定时任务"""
    try:
        job_adder.aps_obj.remove_job(task_id)
        return jsonify({"status": "success", "message": f"任务 '{task_id}' 已被删除。"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # 启动 Flask Web 服务器
    # 在生产环境中，应该使用 Gunicorn 或 uWSGI
    app.run(host='0.0.0.0', port=5000, debug=True)
