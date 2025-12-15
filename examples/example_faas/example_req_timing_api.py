"""
这个是演示funboost.faas 的定时任务管理
"""


import requests

# 添加每10秒执行一次的任务
resp = requests.post("http://127.0.0.1:8000/funboost/add_timing_job", json={
    "queue_name": "test_funboost_faas_queue",
    "trigger": "interval",
    "seconds": 10,
    "job_id": "my_job",
    "kwargs": {"x": 10, "y": 20},
    "job_store_kind": "redis",
    "replace_existing": True,
})
print('add_timing_job',resp.json())

# 获取所有任务
resp = requests.get("http://127.0.0.1:8000/funboost/get_timing_jobs")
print('get_timing_jobs',resp.json())

# 暂停任务
resp = requests.post("http://127.0.0.1:8000/funboost/pause_timing_job", 
    params={"job_id": "my_job", "queue_name": "test_funboost_faas_queue"})
print('pause_timing_job',resp.json())

# # 恢复任务
# resp = requests.post("http://127.0.0.1:8000/funboost/resume_timing_job",
#     params={"job_id": "my_job", "queue_name": "test_funboost_faas_queue"})
# print('resume_timing_job',resp.json())
