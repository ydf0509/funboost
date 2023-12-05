import nb_log
import logging

booster_logger = nb_log.get_logger('funboost.Booster', log_filename='booster.log')
flogger = nb_log.get_logger('funboost', log_filename='funboost.log')

# 开发时候的调试日志，比print方便通过级别一键屏蔽。
develop_logger = nb_log.get_logger('funboost_develop', log_level_int=logging.WARNING, log_filename='funboost_develop.log')
