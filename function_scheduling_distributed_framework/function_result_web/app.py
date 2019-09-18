# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/9/18 0018 14:46
from flask import render_template,Flask
from flask_bootstrap import Bootstrap

app = Flask(__name__)
bootstrap=Bootstrap(app)

@app.route('/test')
def test():
    return render_template('index2.html')


if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.run(debug=True)