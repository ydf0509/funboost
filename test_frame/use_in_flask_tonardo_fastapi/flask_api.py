import flask
from flask_mail import Mail, Message
from function_scheduling_distributed_framework import task_deco, BrokerEnum, PriorityConsumingControlConfig
from function_scheduling_distributed_framework.publishers.base_publisher import RedisAsyncResult

app = flask.Flask(__name__)

app.config.update(
    MAIL_SERVER='MAIL_SERVER',
    MAIL_PORT=678,
    MAIL_USE_TLS=True,
    MAIL_USEERNAME='MAIL_USERNAME',
    MAIL_PASSWORD='MAIL_PASSWORD',
    MAIL_DEFAULT_SENDER=('Grey Li', 'MAIL_USERNAME')
)

mail = Mail(app)


@task_deco(queue_name='flask_test_queue', broker_kind=BrokerEnum.REDIS)
def send_email(msg):
    """
    演示一般性大部分任务，如果函数不需要使用app上下文
    :param msg:
    :return:
    """
    print(f'发送邮件  {msg}')


@task_deco(queue_name='flask_test_queue', broker_kind=BrokerEnum.REDIS)
def send_main_with_app_context(msg):
    """
    演示使用 flask_mail ，此包需要用到app上下文
    :param msg:
    :return:
    """
    with app.app_context():
        # 这个Message类需要读取flask的配置里面邮件发件人等信息，由于发布和消费不是同一太机器或者进程，必须使用上下文才嫩知道邮件配置
        message = Message(subject='title', recipients=['367224698@qq.com'], body=msg)
        mail.send(message)



#############################  如果你想再封装一点，就加个通用上下文装饰器开始  ################################

def your_app_context_deco(flask_appx: flask.Flask):
    def _deco(fun):
        def __deco(*args, **kwargs):
            with flask_appx.app_context():
                return fun(*args, **kwargs)

        return _deco

    return _deco


@task_deco(queue_name='flask_test_queue', broker_kind=BrokerEnum.REDIS)
@your_app_context_deco(app)
def send_main_with_app_context2(msg):
    """
    演示使用 flask_mail ，此包需要用到app上下文
    :param msg:
    :return:
    """
    message = Message(subject='title', recipients=['367224698@qq.com'], body=msg)
    mail.send(message)

#############################  如果你想再封装一点，就加个通用上下文装饰器结束  ################################


# 这是falsk接口，在接口中发布任务到消息队列
@app.route('/')
def send_email_api():
    """
    :return:
    """
    # 如果前端不关注结果，只是把任务发到中间件，那就使用  send_email.push(msg='邮件内容') 就可以了。
    async_result = send_email.publish(dict(msg='邮件内容'), priority_control_config=PriorityConsumingControlConfig(is_using_rpc_mode=True))  # type: RedisAsyncResult
    return async_result.task_id
    # return async_result.result  # 不推荐，这种会阻塞接口，一般是采用另外写一个ajax接口带着task_id去获取结果，后端实现方式为 RedisAsyncResult(task_id,timeout=30).result

    # 如果要结果，最好的方式并不是轮询ajax，使用mqtt是最好的方案，前端订阅 mqtt topic，消费函数里面把结果发布到mqtt的topic。
    # 这种方式实现难度暴击使用后端导入一大推websocket相关的模块，性能也很好单个mqtt支持几十万长连接暴击python+websocket，实现上页更简单，并且实时性暴击ajax轮询。


if __name__ == '__main__':
    app.run()
