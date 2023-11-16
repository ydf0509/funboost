# noinspection PyUnresolvedReferences
import atexit

import nb_log
# noinspection PyUnresolvedReferences
from nb_log import get_logger, nb_print

'''
set_frame_config 这行要放在所有导入其他代码之前最好,以便防止其他项目提前 from funboost.funboost_config_deafult import xx ,
如果是 from funboost import funboost_config_deafult,在函数内部使用他的配置就没事,但最后不要让其他模块在 set_frame_config 之前导入.
set_frame_config这个模块的 use_config_form_funboost_config_module() 是核心,把用户的funboost_config.py的配置覆盖到funboost_config_deafult模块了

这段注释说明和使用的用户无关.
'''

from funboost.set_frame_config import  show_frame_config

# noinspection PyUnresolvedReferences
from funboost.utils.dependency_packages_in_pythonpath import add_to_pythonpath  # 这是把 dependency_packages_in_pythonpath 添加到 PYTHONPATH了。
from funboost.utils import monkey_patches

from funboost.funboost_config_deafult import BoostDecoratorDefaultParams,FunboostCommonConfig,BrokerConnConfig

from funboost.core.fabric_deploy_helper import fabric_deploy, kill_all_remote_tasks
from funboost.utils.paramiko_util import ParamikoFolderUploader

from funboost.consumers.base_consumer import (ExceptionForRequeue, ExceptionForRetry, ExceptionForPushToDlxqueue,
                                              AbstractConsumer, ConsumersManager,
                                              FunctionResultStatusPersistanceConfig,
                                              wait_for_possible_has_finish_all_tasks_by_conusmer_list,
                                              FunctionResultStatus)
from funboost.core.active_cousumer_info_getter import ActiveCousumerProcessInfoGetter
from funboost.core.msg_result_getter import HasNotAsyncResult, ResultFromMongo
from funboost.publishers.base_publisher import (PriorityConsumingControlConfig,
                                                AbstractPublisher, AsyncResult, AioAsyncResult)
from funboost.factories.broker_kind__publsiher_consumer_type_map import register_custom_broker
from funboost.factories.publisher_factotry import get_publisher
from funboost.factories.consumer_factory import get_consumer

from funboost.timing_job import fsdf_background_scheduler, timing_publish_deco, funboost_aps_scheduler
from funboost.constant import BrokerEnum, ConcurrentModeEnum

from funboost.core.booster import boost, Booster,BoostersManager
# from funboost.core.get_booster import get_booster, get_or_create_booster, get_boost_params_and_consuming_function
from funboost.core.booster import BoostersManager
from funboost.core.kill_remote_task import RemoteTaskKiller
from funboost.funboost_config_deafult import BrokerConnConfig,FunboostCommonConfig,BoostDecoratorDefaultParams

# from funboost.core.exit_signal import set_interrupt_signal_handler
from funboost.core.helper_funs import run_forever

from funboost.utils.ctrl_c_end import ctrl_c_recv
from funboost.utils.redis_manager import RedisMixin
# atexit.register(ctrl_c_recv)  # 还是需要用户自己在代码末尾加才可以.
# set_interrupt_signal_handler()

# 有的包默认没加handlers，原始的日志不漂亮且不可跳转不知道哪里发生的。这里把warnning级别以上的日志默认加上handlers。
# nb_log.get_logger(name='', log_level_int=30, log_filename='pywarning.log')

__version__ = "30.4"