def _try_get_user_funboost_common_config(funboost_common_conf_field:str):
    try:
        import funboost_config  # 第一次启动funboost前还没这个文件,或者还没有初始化配置之前,就要使用使用配置.
        return getattr(funboost_config.FunboostCommonConfig,funboost_common_conf_field)
    except Exception as e:
        # print(e)
        return None