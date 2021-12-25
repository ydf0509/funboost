import nb_log
from funboost import funboost_config_deafult

#开发时候的调试日志，比print方便通过级别一键屏蔽。
develop_logger = nb_log.get_logger('fsdf_develop', log_level_int=funboost_config_deafult.FSDF_DEVELOP_LOG_LEVEL)
