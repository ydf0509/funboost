

from funboost.core.active_cousumer_info_getter import QueuesConusmerParamsGetter
from funboost.funboost_web_manager.app import start_funboost_web_manager


if __name__ == '__main__':
    start_funboost_web_manager(
        port=27010,
        debug=True,
        care_project_name='test_project1',
        block=True
        )

