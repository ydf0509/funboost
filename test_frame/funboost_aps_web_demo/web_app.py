from flask import Flask
from funboost import ApsJobAdder
from funcs import fun_sum

app = Flask(__name__)

@app.route('/', methods=['get'])
def index():
    return '演示添加funboost定时任务'

@app.route('/add_job', methods=['get'])
def api_add_job():
    """
    接口中添加apscheduler定时任务到中，使用reids作为jobstroes。 is_auto_paused=True意思是暂停aps执行任务，因为这里不需要真的执行任务，只负责增删改查定时任务到redis中。
    
    然你也可以is_auto_paused=False，这样aps对象就会不仅负责天极爱定时任务到redis还会负责执行redis中的任务。
    因为funboost的 apschrduler是定制的，扫描定时任务时候使用了redis分布式锁，所以不用担心多次启动apschrduler对象造成重复执行定时任务
    """
    ApsJobAdder(fun_sum,job_store_kind='redis',is_auto_paused=True).add_push_job(
        args=(1, 2),
        trigger='interval',  # 使用日期触发器
        seconds=10,
        id='add_numbers_job', # 任务ID
        replace_existing=True,
        name='add_numbers_job',
    )
    return 'ok'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5009)
