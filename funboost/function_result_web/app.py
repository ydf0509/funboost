# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/9/18 0018 14:46
import threading

import sys


import os
# print("PYTHONPATH:", os.environ.get('PYTHONPATH'))


import datetime
import json
import traceback

from funboost.core.func_params_model import PriorityConsumingControlConfig

"""
pip install Flask flask_bootstrap  flask_wtf  wtforms flask_login       
"""
from flask import render_template, Flask, request, url_for, jsonify, flash, redirect
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_login import login_user, logout_user, login_required, LoginManager, UserMixin

import nb_log
from funboost import nb_print,ActiveCousumerProcessInfoGetter,BoostersManager,PublisherParams,RedisMixin
from funboost.function_result_web.functions import get_cols, query_result, get_speed, Statistic
from funboost.function_result_web import functions as app_functions
from funboost.core.active_cousumer_info_getter import QueueConusmerParamsGetter
from funboost.constant import RedisKeys

app = Flask(__name__)
app.secret_key = 'mtfy54321'
app.config['JSON_AS_ASCII'] = False
bootstrap = Bootstrap(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.login_message = 'Access denied.'
login_manager.init_app(app)



class User(UserMixin):
    pass


users = [
    {'id': 'Tom', 'user_name': 'Tom', 'password': '111111'},
    {'id': 'user', 'user_name': 'user', 'password': 'mtfy123'},
    {'id': 'admin', 'user_name': 'admin', 'password': '123456'}
]


nb_log.get_logger('flask',log_filename='flask.log')
nb_log.get_logger('werkzeug',log_filename='werkzeug.log')

def query_user(user_name):
    for user in users:
        if user_name == user['user_name']:
            return user


@login_manager.user_loader
def load_user(user_id):
    if query_user(user_id) is not None:
        curr_user = User()
        curr_user.id = user_id
        return curr_user


class LoginForm(FlaskForm):
    user_name = StringField(u'用户名', validators=[DataRequired(), Length(3, 64)])
    password = PasswordField(u'密码', validators=[DataRequired(), Length(3, 64)])
    remember_me = BooleanField(u'记住我')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':

        # nb_print(form.validate())
        # nb_print(form.password.data)
        # nb_print(form.user_name.data)
        # nb_print(form.user_name.errors)
        # nb_print(form.password.errors)
        if form.validate_on_submit():
            user = query_user(form.user_name.data)
            if user is not None and request.form['password'] == user['password']:
                curr_user = User()
                curr_user.id = form.user_name.data

                # 通过Flask-Login的login_user方法登录用户
                nb_print(form.remember_me.data)
                login_user(curr_user, remember=form.remember_me.data, duration=datetime.timedelta(days=7))

                return redirect(url_for('index'))

            flash('用户名或密码错误', category='error')

            # if form.user_name.data == 'user' and form.password.data == 'mtfy123':
            #     login_user(form.user_name.data, form.remember_me.data)
            #     return redirect(url_for('index'))
            # else:
            #     flash('账号或密码错误',category='error')
            #     return render_template('login4.html', form=form)

    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    page = request.args.get('page')
    return render_template('index.html', page=page)


@app.route('/query_cols')
@login_required
def query_cols_view():
    nb_print(request.args)
    return jsonify(get_cols(request.args.get('col_name_search')))


@app.route('/query_result')
@login_required
def query_result_view():

    return jsonify(query_result(**request.values.to_dict()))


@app.route('/speed_stats')
@login_required
def speed_stats():
    return jsonify(get_speed(**request.values.to_dict()))


@app.route('/speed_statistic_for_echarts')
@login_required
def speed_statistic_for_echarts():
    stat = Statistic(request.args.get('col_name'))
    stat.build_result()
    return jsonify(stat.result)

@app.route('/tpl/<template>')
@login_required
def serve_template(template):
    # 安全检查：确保只能访问templates目录下的html文件
    if not template.endswith('.html'):
        return 'Invalid request', 400
    try:
        return render_template(template)
    except Exception as e:
        return f'Template not found: {template}', 404


@app.route('/running_consumer/hearbeat_info_by_queue_name')
def hearbeat_info_by_queue_name():
    if request.args.get('queue_name') in ('所有',None):
        info_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_queue_name()
        ret_list = []
        for queue_name,dic in info_map.items():
            ret_list.extend(dic)
        return jsonify(ret_list)
    else:
        return jsonify(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_queue_name(request.args.get('queue_name')))
    
        

@app.route('/running_consumer/hearbeat_info_by_ip')
def hearbeat_info_by_ip():
    if request.args.get('ip') in ('所有',None):
        info_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_ip()
        ret_list = []
        for queue_name,dic in info_map.items():
            ret_list.extend(dic)
        return jsonify(ret_list)
    else:
        return jsonify(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_ip(request.args.get('ip')))


@app.route('/running_consumer/hearbeat_info_partion_by_queue_name')
def hearbeat_info_partion_by_queue_name():
    info_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_queue_name()
    ret_list = []
    total_count = 0
    for k,v in info_map.items():
        ret_list.append({'collection_name':k,'count':len(v)})
        total_count +=len(v)
    ret_list = sorted(ret_list, key=lambda x: x['collection_name'])
    ret_list.insert(0,{'collection_name':'所有','count':total_count})
    return jsonify(ret_list)

@app.route('/running_consumer/hearbeat_info_partion_by_ip')
def hearbeat_info_partion_by_ip():
    info_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_ip()
    ret_list = []
    total_count = 0
    for k,v in info_map.items():
        ret_list.append({'collection_name':k,'count':len(v)})
        total_count +=len(v)
    ret_list = sorted(ret_list, key=lambda x: x['collection_name'])
    ret_list.insert(0,{'collection_name':'所有','count':total_count})
    print(ret_list)
    return jsonify(ret_list)


@app.route('/queue/params_and_active_consumers')
def get_queue_params_and_active_consumers():
    return jsonify(QueueConusmerParamsGetter().get_queue_params_and_active_consumers())




@app.route('/queue/clear/<broker_kind>/<queue_name>',methods=['POST'])
def clear_queue(broker_kind,queue_name):
    publisher = BoostersManager.get_cross_project_publisher(PublisherParams(queue_name=queue_name, broker_kind=broker_kind, publish_msg_log_use_full_msg=True))
    publisher.clear()
    return jsonify({'success':True})

@app.route('/queue/pause/<queue_name>', methods=['POST'])
def pause_cousume(queue_name):
    RedisMixin().redis_db_frame.hset(RedisKeys.REDIS_KEY_PAUSE_FLAG, queue_name,'1')
    return jsonify({'success':True})

@app.route('/queue/resume/<queue_name>',methods=['POST'])
def resume_consume(queue_name):
    RedisMixin().redis_db_frame.hset(RedisKeys.REDIS_KEY_PAUSE_FLAG, queue_name,'0')
    return jsonify({'success':True})

@app.route('/queue/get_msg_num_all_queues',methods=['GET'])
def get_msg_num_all_queues():
    """这个是通过消费者周期每隔10秒上报到redis的，性能好。不需要实时获取每个消息队列，直接从redis读取所有队列的消息数量"""
    return jsonify(QueueConusmerParamsGetter().get_msg_num(ignore_report_ts=True))

@app.route('/queue/message_count/<broker_kind>/<queue_name>')
def get_message_count(broker_kind,queue_name):
    """这个是实时获取每个消息队列的消息数量，性能差，但是可以实时获取每个消息队列的消息数量"""
    queue_params = QueueConusmerParamsGetter().get_queue_params()
    for queue_namex,params in queue_params.items():
        if params['broker_kind'] == broker_kind and queue_namex == queue_name:
            publisher = BoostersManager.get_cross_project_publisher(
                PublisherParams(queue_name=queue_name, 
                                 broker_kind=broker_kind,
                                 broker_exclusive_config=params['broker_exclusive_config'],
                                 publish_msg_log_use_full_msg=True))
            return jsonify({'count':publisher.get_message_count(),'success':True})
    return jsonify({'success':False,'msg':f'队列{queue_name}不存在'})

    publisher = BoostersManager.get_cross_project_publisher(PublisherParams(queue_name=queue_name, broker_kind=broker_kind, publish_msg_log_use_full_msg=True))
    return jsonify({'count':publisher.get_message_count(),'success':True})
        
@app.route('/rpc/rpc_call',methods=['POST'])
def rpc_call():
    """
    class MsgItem(BaseModel):
        queue_name: str  # 队列名
        msg_body: dict  # 消息体,就是boost函数的入参字典,例如 {"x":1,"y":2}
        need_result: bool = False  # 发布消息后,是否需要返回结果
        timeout: int = 60  # 等待结果返回的最大等待时间.


    class PublishResponse(BaseModel):
        succ: bool
        msg: str
        status_and_result: typing.Optional[dict] = None  # 消费函数的消费状态和结果.
        task_id:str
    """
    
    msg_item = request.get_json()
    return jsonify(app_functions.rpc_call(**msg_item))
    
@app.route('/rpc/get_result_by_task_id',methods=['GET'])
def get_result_by_task_id():
    res = app_functions.get_result_by_task_id(task_id=request.args.get('task_id'),
                                                          timeout=request.args.get('timeout') or 60)
    if res['status_and_result'] is None:
        return jsonify({'succ':False,'msg':'task_id不存在或者超时或者结果已经过期'})
    return jsonify(res)
   

def start_funboost_web_manager(host='0.0.0.0', port=27018,block=False):
    print('start_funboost_web_manager , sys.path :', sys.path)
    def _start_funboost_web_manager():
        app.run(debug=False, threaded=True, host=host, port=port)
    QueueConusmerParamsGetter().cycle_get_queue_params_and_active_consumers_and_report()
    if block is  True:
        _start_funboost_web_manager()
    else:
        threading.Thread(target=_start_funboost_web_manager).start()
        
        
        
if __name__ == '__main__':
    # app.jinja_env.auto_reload = True
    # with app.test_request_context():
    #     print(url_for('query_cols_view'))
    QueueConusmerParamsGetter().cycle_get_queue_params_and_active_consumers_and_report(daemon=True)
    app.run(debug=False, threaded=True, host='0.0.0.0', port=27018)

    
    '''
    funboost web manager 启动方式：

    web代码在funboost包里面，所以可以直接使用命令行运行起来，不需要用户现亲自下载web代码就可以直接运行。
    
    第一步： 设置 PYTHONPATH 为你的项目根目录
    export PYTHONPATH=你的项目根目录 (这么做是为了这个web可以读取到你项目根目录下的 funboost_config.py里面的配置)
    (怎么设置环境变量应该不需要我来教，环境变量都没听说过太low了)
      例如 export PYTHONPATH=/home/ydf/codes/ydfhome
      或者 export PYTHONPATH=./   (./是相对路径，前提是已近cd到你的项目根目录了，也可以写绝对路径全路径)
      win cmd 设置环境变量语法是 set PYTHONPATH=/home/ydf/codes/ydfhome   
      win powershell 语法是  $env:PYTHONPATH = "/home/ydf/codes/ydfhome"   

    第二步： 启动flask app   
    win上这么做 python3 -m funboost.function_result_web.app 

    linux上可以这么做性能好一些，也可以按win的做。
    gunicorn -w 4 --threads=30 --bind 0.0.0.0:27018 funboost.function_result_web.app:app
    '''
