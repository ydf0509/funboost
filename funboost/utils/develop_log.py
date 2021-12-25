import nb_log
from funboost import frame_config

#开发时候的调试日志，比print方便通过级别一键屏蔽。
develop_logger = nb_log.get_logger('fsdf_develop',log_level_int=frame_config.FSDF_DEVELOP_LOG_LEVEL)
