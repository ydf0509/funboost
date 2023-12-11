# from pydantic import BaseModel, validator, root_validator
#
# import nb_log
# from nb_log import LoggerMixin
#
#
# # class FunctionResultStatusPersistanceConfig(LoggerMixin):
# #     def __init__(self, is_save_status: bool, is_save_result: bool, expire_seconds: int = 7 * 24 * 3600, is_use_bulk_insert=False):
# #         """
# #         :param is_save_status:
# #         :param is_save_result:
# #         :param expire_seconds: 设置统计的过期时间，在mongo里面自动会移除这些过期的执行记录。
# #         :param is_use_bulk_insert : 是否使用批量插入来保存结果，批量插入是每隔0.5秒钟保存一次最近0.5秒内的所有的函数消费状态结果，始终会出现最后0.5秒内的执行结果没及时插入mongo。为False则，每完成一次函数就实时写入一次到mongo。
# #         """
# #
# #         if not is_save_status and is_save_result:
# #             raise ValueError(f'你设置的是不保存函数运行状态但保存函数运行结果。不允许你这么设置')
# #         self.is_save_status = is_save_status
# #         self.is_save_result = is_save_result
# #         if expire_seconds > 10 * 24 * 3600:
# #             self.logger.warning(f'你设置的过期时间为 {expire_seconds} ,设置的时间过长。 ')
# #         self.expire_seconds = expire_seconds
# #         self.is_use_bulk_insert = is_use_bulk_insert
# #
# #     def to_dict(self):
# #         return {"is_save_status": self.is_save_status,
# #
# #                 'is_save_result': self.is_save_result, 'expire_seconds': self.expire_seconds}
# #
# #     def __str__(self):
# #         return f'<FunctionResultStatusPersistanceConfig> {id(self)} {self.to_dict()}'
# #
#
#
