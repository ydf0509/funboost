import time

import flask

app =flask.Flask(__name__)


@app.get('/')
def index():
    time.sleep(10)
    return 'hi'

if __name__ == '__main__':
    app.run()