# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 9:48


from funboost.utils.dependency_packages_in_pythonpath import add_to_pythonpath

from nb_log import (LogManager, simple_logger, defaul_logger, LoggerMixin, LoggerLevelSetterMixin,
                    LoggerMixinDefaultWithFileHandler,nb_print,patch_print,reverse_patch_print,get_logger)

# from funboost.utils.redis_manager import RedisMixin

from funboost.utils.json_helper import monkey_patch_json


#################以下为打猴子补丁#####################
monkey_patch_json()





