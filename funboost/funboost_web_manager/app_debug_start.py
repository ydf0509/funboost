


from funboost.funboost_web_manager.app import (
    start_funboost_web_manager,
    app,
    CareProjectNameEnv,
    QueuesConusmerParamsGetter,
)



CareProjectNameEnv.set('test_project1')


a=4

if __name__ == '__main__':
    QueuesConusmerParamsGetter().cycle_get_queues_params_and_active_consumers_and_report(daemon=True)
    # 关闭 use_reloader，使用外部 watchdog 重载器 (flask_realod.py)
    app.run(debug=True, use_reloader=False, threaded=True, host='0.0.0.0', port=27011)
    
    """
    test_frame/test_watchdog_broker/flask_realod.py 中去自动重新启动flask
    
    自带的use_reloader老是代码改到一半，就重启了报错，导致之后无法自动重启和恢复。
    """


   
