

from funboost.core.active_cousumer_info_getter import QueueConusmerParamsGetter
from funboost.function_result_web.app import app


if __name__ == '__main__':
    QueueConusmerParamsGetter().cycle_get_queue_params_and_active_consumers_and_report(daemon=True)
    app.run(debug=True, threaded=True, host='0.0.0.0', port=27019)

