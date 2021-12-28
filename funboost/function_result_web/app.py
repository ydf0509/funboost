# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/9/18 0018 14:46

import datetime
import json

from flask import render_template, Flask, request, url_for, jsonify, flash, redirect
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_login import login_user, logout_user, login_required, LoginManager, UserMixin

from funboost import nb_print
from funboost.function_result_web.functions import get_cols, query_result, get_speed, Statistic

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

        nb_print(form.validate())
        nb_print(form.password.data)
        nb_print(form.user_name.data)
        nb_print(form.user_name.errors)
        nb_print(form.password.errors)
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
    return render_template('index.html')


@app.route('/query_cols')
@login_required
def query_cols_view():
    nb_print(request.args)
    return jsonify(get_cols(request.args.get('col_name_search')))


@app.route('/query_result')
@login_required
def query_result_view():
    nb_print(request.values.to_dict())
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


if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    with app.test_request_context():
        print(url_for('query_cols_view'))

    app.run(debug=True, threaded=True, host='0.0.0.0', port=27018)

    '''
    # 第一步 export PYTHONPATH=你的项目根目录 ，这么做是为了这个web可以读取到你项目根目录下的 funboost_config.py里面的配置
    # 例如 export PYTHONPATH=/home/ydf/codes/ydfhome
      或者  export PYTHONPATH=./   (./是相对路径，前提是已近cd到你的项目根目录了，也可以写绝对路径全路径)
    
    第二步   
    win上这么做 python3 -m funboost.function_result_web.app 
    
    linux上可以这么做性能好一些，也可以按win的做。
    gunicorn -w 4 --threads=30 --bind 0.0.0.0:27018 funboost.function_result_web.app:app
    '''
