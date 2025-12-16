

from funboost.core.active_cousumer_info_getter import QueuesConusmerParamsGetter
from funboost.funboost_web_manager.app import start_funboost_web_manager,app,CareProjectNameEnv



if __name__ == '__main__':
    # start_funboost_web_manager(
    #     port=27011,
    #     debug=True,
    #     care_project_name='test_project1',
    #     block=True
    #     )
    app.config.update(
    TEMPLATES_AUTO_RELOAD=True,  # html / jinja 自动刷新
    )
    CareProjectNameEnv.set('test_project1')
    QueuesConusmerParamsGetter().cycle_get_queues_params_and_active_consumers_and_report()
    app.run(debug=True,      # 保留 debug（异常页面、调试器）
        use_reloader=False,  # ❗关键：禁止 py 文件触发重启
     threaded=True, host='0.0.0.0', port=27012)

