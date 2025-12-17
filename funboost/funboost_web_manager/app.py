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
import typing
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
from funboost import (
    nb_print,
    ActiveCousumerProcessInfoGetter,
    # BoostersManager,  # 未使用
    # PublisherParams,  # 未使用
    # RedisMixin,  # 已废弃的 pause/resume 路由使用，现已注释
)
from funboost.funboost_web_manager.functions import (
    get_cols,
    query_result,
    get_speed,
    # Statistic,  # 已废弃，前端不再使用 speed_statistic_for_echarts 路由
)
from funboost.funboost_web_manager import functions as app_functions
from funboost.core.active_cousumer_info_getter import (
    QueuesConusmerParamsGetter,
    SingleQueueConusmerParamsGetter,
    CareProjectNameEnv,
)
# from funboost.constant import RedisKeys  # 已废弃的 pause/resume 路由使用，现已注释
from funboost.faas import flask_blueprint

app = Flask(__name__)
app.secret_key = "mtfy54321"
app.config["JSON_AS_ASCII"] = False
bootstrap = Bootstrap(app)
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "info"
login_manager.login_message = "Access denied."
login_manager.init_app(app)


# 定时任务用faas这里面自带的flask蓝图，因为通用的faas接口是2025年12月才有的功能，老的flask接口是在这里单独开发的。
app.register_blueprint(flask_blueprint)  



class User(UserMixin):
    pass


users = [
    {"id": "Tom", "user_name": "Tom", "password": "111111"},
    {"id": "user", "user_name": "user", "password": "mtfy123"},
    {"id": "admin", "user_name": "admin", "password": "123456"},
]


nb_log.get_logger("flask", log_filename="flask.log")
nb_log.get_logger("werkzeug", log_filename="werkzeug.log")


def query_user(user_name):
    for user in users:
        if user_name == user["user_name"]:
            return user


@login_manager.user_loader
def load_user(user_id):
    if query_user(user_id) is not None:
        curr_user = User()
        curr_user.id = user_id
        return curr_user


class LoginForm(FlaskForm):
    user_name = StringField("用户名", validators=[DataRequired(), Length(3, 64)])
    password = PasswordField("密码", validators=[DataRequired(), Length(3, 64)])
    remember_me = BooleanField("记住我")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "POST":
        # nb_print(form.validate())
        # nb_print(form.password.data)
        # nb_print(form.user_name.data)
        # nb_print(form.user_name.errors)
        # nb_print(form.password.errors)
        if form.validate_on_submit():
            user = query_user(form.user_name.data)
            if user is not None and request.form["password"] == user["password"]:
                curr_user = User()
                curr_user.id = form.user_name.data

                # 通过Flask-Login的login_user方法登录用户
                nb_print(form.remember_me.data)
                login_user(
                    curr_user,
                    remember=form.remember_me.data,
                    duration=datetime.timedelta(days=7),
                )

                return redirect(url_for("index"))

            flash("用户名或密码错误", category="error")

            # if form.user_name.data == 'user' and form.password.data == 'mtfy123':
            #     login_user(form.user_name.data, form.remember_me.data)
            #     return redirect(url_for('index'))
            # else:
            #     flash('账号或密码错误',category='error')
            #     return render_template('login4.html', form=form)

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    page = request.args.get("page")
    return render_template("index.html", page=page)


@app.route("/query_cols")
@login_required
def query_cols_view():
    nb_print(request.args)
    return jsonify(get_cols(request.args.get("col_name_search")))


@app.route("/query_result")
@login_required
def query_result_view():
    return jsonify(query_result(**request.values.to_dict()))


@app.route("/speed_stats")
@login_required
def speed_stats():
    return jsonify(get_speed(**request.values.to_dict()))


# 以下路由已废弃，功能已迁移到 consume_speed_curve，前端不再使用
# @app.route("/speed_statistic_for_echarts")
# @login_required
# def speed_statistic_for_echarts():
#     stat = Statistic(request.args.get("col_name"))
#     stat.build_result()
#     return jsonify(stat.result)


@app.route("/consume_speed_curve")
@login_required
def consume_speed_curve():
    """获取消费速率曲线数据"""
    from funboost.funboost_web_manager.functions import get_consume_speed_curve
    col_name = request.args.get("col_name")
    start_time = request.args.get("start_time")
    end_time = request.args.get("end_time")
    granularity = request.args.get("granularity", "auto")
    
    if not col_name or not start_time or not end_time:
        return jsonify({"error": "缺少必要参数: col_name, start_time, end_time"})
    
    try:
        result = get_consume_speed_curve(col_name, start_time, end_time, granularity)
        return jsonify(result)
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()})


@app.route("/tpl/<template>")
@login_required
def serve_template(template):
    # 安全检查：确保只能访问templates目录下的html文件
    if not template.endswith(".html"):
        return "Invalid request", 400
    try:
        return render_template(template)
    except Exception as e:
        return f"Template not found: {template}", 404


@app.route("/running_consumer/hearbeat_info_by_queue_name")
def hearbeat_info_by_queue_name():
    queue_name = request.args.get("queue_name")
    if queue_name in ("所有", None, ""):
        info_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_queue_name()
        ret_list = []
        for queue_name, dic in info_map.items():
            ret_list.extend(dic)
        return jsonify(ret_list)
    else:
        return jsonify(
            ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_queue_name(queue_name)
        )


@app.route("/running_consumer/hearbeat_info_by_ip")
def hearbeat_info_by_ip():
    ip = request.args.get("ip")
    if ip in ("所有", None, ""):
        info_map = (
            ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_ip()
        )
        ret_list = []
        for queue_name, dic in info_map.items():
            ret_list.extend(dic)
        return jsonify(ret_list)
    else:
        return jsonify(
            ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_ip(ip)
        )


@app.route("/running_consumer/hearbeat_info_partion_by_queue_name")
def hearbeat_info_partion_by_queue_name():
    info_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_queue_name()
    ret_list = []
    total_count = 0
    for k, v in info_map.items():
        ret_list.append({"collection_name": k, "count": len(v)})
        total_count += len(v)
    ret_list = sorted(ret_list, key=lambda x: x["collection_name"])
    ret_list.insert(0, {"collection_name": "所有", "count": total_count})
    return jsonify(ret_list)


@app.route("/running_consumer/hearbeat_info_partion_by_ip")
def hearbeat_info_partion_by_ip():
    info_map = ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_ip()
    ret_list = []
    total_count = 0
    for k, v in info_map.items():
        ret_list.append({"collection_name": k, "count": len(v)})
        total_count += len(v)
    ret_list = sorted(ret_list, key=lambda x: x["collection_name"])
    ret_list.insert(0, {"collection_name": "所有", "count": total_count})
    print(ret_list)
    return jsonify(ret_list)


@app.route("/queue/params_and_active_consumers")
def get_queues_params_and_active_consumers():
    return jsonify(
        QueuesConusmerParamsGetter().get_queues_params_and_active_consumers()
    )





# 以下两个路由已废弃，前端没有使用（暂停/恢复消费功能可能在其他地方实现）
# @app.route("/queue/pause/<queue_name>", methods=["POST"])
# def pause_cousume(queue_name):
#     RedisMixin().redis_db_frame.hset(RedisKeys.REDIS_KEY_PAUSE_FLAG, queue_name, "1")
#     return jsonify({"success": True})


# @app.route("/queue/resume/<queue_name>", methods=["POST"])
# def resume_consume(queue_name):
#     RedisMixin().redis_db_frame.hset(RedisKeys.REDIS_KEY_PAUSE_FLAG, queue_name, "0")
#     return jsonify({"success": True})


@app.route("/queue/get_msg_num_all_queues", methods=["GET"])
def get_msg_num_all_queues():
    """这个是通过消费者周期每隔10秒上报到redis的，性能好。不需要实时获取每个消息队列，直接从redis读取所有队列的消息数量"""
    return jsonify(QueuesConusmerParamsGetter().get_msg_num(ignore_report_ts=True))



@app.route("/queue/get_time_series_data/<queue_name>", methods=["GET"])
def get_time_series_data_by_queue_name(
    queue_name,
):
    """_summary_

    Args:
        queue_name (_type_): _description_

    Returns:
        _type_: _description_

    返回例如  [{'report_data': {'pause_flag': -1, 'msg_num_in_broker': 936748, 'history_run_count': '150180', 'history_run_fail_count': '46511', 'all_consumers_last_x_s_execute_count': 7, 'all_consumers_last_x_s_execute_count_fail': 0, 'all_consumers_last_x_s_avarage_function_spend_time': 3.441, 'all_consumers_avarage_function_spend_time_from_start': 4.598, 'all_consumers_total_consume_count_from_start': 1296, 'all_consumers_total_consume_count_from_start_fail': 314, 'report_ts': 1749617360.597841}, 'report_ts': 1749617360.597841}, {'report_data': {'pause_flag': -1, 'msg_num_in_broker': 936748, 'history_run_count': '150184', 'history_run_fail_count': '46514', 'all_consumers_last_x_s_execute_count': 7, 'all_consumers_last_x_s_execute_count_fail': 0, 'all_consumers_last_x_s_avarage_function_spend_time': 3.441, 'all_consumers_avarage_function_spend_time_from_start': 4.599, 'all_consumers_total_consume_count_from_start': 1299, 'all_consumers_total_consume_count_from_start_fail': 316, 'report_ts': 1749617370.628166}, 'report_ts': 1749617370.628166}]
    """
    # 获取前端传递的参数
    start_ts = request.args.get("start_ts")
    end_ts = request.args.get("end_ts")
    curve_samples_count = request.args.get("curve_samples_count")

    # 如果前端指定了采样点数，使用前端的值
    if curve_samples_count:
        try:
            curve_samples_count = int(curve_samples_count)
            # 验证值是否在允许的范围内
            allowed_values = [60, 120, 180, 360, 720, 1440, 8640]
            if curve_samples_count not in allowed_values:
                curve_samples_count = 360  # 默认值
        except (ValueError, TypeError):
            curve_samples_count = 360  # 默认值
    else:
        # 如果前端没有指定，使用默认值
        curve_samples_count = 360

    return jsonify(
        SingleQueueConusmerParamsGetter(queue_name).get_one_queue_time_series_data(
            start_ts, end_ts, curve_samples_count
        )
    )




def start_funboost_web_manager(
    host="0.0.0.0",
    port=27018,
    block=False,
    debug=False,
    care_project_name: typing.Optional[str] = None,
):
    
    if care_project_name is not None:
       CareProjectNameEnv.set(care_project_name)
    print("start_funboost_web_manager , sys.path :", sys.path)

    def _start_funboost_web_manager():
        app.run(debug=debug, threaded=True, host=host, port=port)

    QueuesConusmerParamsGetter().cycle_get_queues_params_and_active_consumers_and_report()
    if block is True:
        _start_funboost_web_manager()
    else:
        threading.Thread(target=_start_funboost_web_manager).start()


if __name__ == "__main__":
    # app.jinja_env.auto_reload = True
    # with app.test_request_context():
    #     print(url_for('query_cols_view'))
    start_funboost_web_manager(debug=False)

    """
    funboost web manager 启动方式1：

    web代码在funboost包里面，所以可以直接使用命令行运行起来，不需要用户现亲自下载web代码就可以直接运行。
    
    第一步： 设置 PYTHONPATH 为你的项目根目录
    export PYTHONPATH=你的项目根目录 (这么做是为了这个web可以读取到你项目根目录下的 funboost_config.py里面的配置)
    (怎么设置环境变量应该不需要我来教，环境变量都没听说过太low了)
      例如 export PYTHONPATH=/home/ydf/codes/ydfhome
      或者 export PYTHONPATH=./   (./是相对路径，前提是已近cd到你的项目根目录了，也可以写绝对路径全路径)
      win cmd 设置环境变量语法是 set PYTHONPATH=/home/ydf/codes/ydfhome   
      win powershell 语法是  $env:PYTHONPATH = "/home/ydf/codes/ydfhome"   

    第二步： 启动flask app   
    win上这么做 python3 -m funboost.funboost_web_manager.app 

    linux上可以这么做性能好一些，也可以按win的做。
    gunicorn -w 4 --threads=30 --bind 0.0.0.0:27018 funboost.funboost_web_manager.app:app
    """

    """
    funboost web manager 启动方式2：
    在python代码中直接启动：

    ```python
    from  funboost.funboost_web_manager.app import start_funboost_web_manager
    start_funboost_web_manager()
    ```
    
    """
