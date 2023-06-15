import time
import nb_log
import flask

app =flask.Flask(__name__)


@app.get('/')
def index():
    time.sleep(20)
    print(555555)
    return 'hi'

if __name__ == '__main__':
    app.run()