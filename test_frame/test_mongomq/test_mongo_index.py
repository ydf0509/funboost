import datetime

from funboost.utils.mongo_util import MongoMixin


# col = MongoMixin().get_mongo_collection('task_status','test_ex')
#
# col.insert_one({'a':1,'utime':datetime.datetime.utcnow()})
#
# col.create_index([("utime", 1)],
#                                              expireAfterSeconds=3000)

col = MongoMixin().get_mongo_collection('task_status','test_queue77h6')

index_dict = col.index_information()
print(index_dict)
'''
 {'_id_': {'v': 2, 'key': [('_id', 1)]}, 'insert_time_str_-1': {'v': 2, 'key': [('insert_time_str', -1)]}, 'insert_time_-1': {'v': 2, 'key': [('insert_time', -1)]}, 'params_str_text': {'v': 2, 'key': [('_fts', 'text'), ('_ftsx', 1)], 'weights': SON([('params_str', 1)]), 'default_language': 'english', 'language_override': 'language', 'textIndexVersion': 3}, 'success_1': {'v': 2, 'key': [('success', 1)]}, 'utime_1': {'v': 2, 'key': [('utime', 1)], 'expireAfterSeconds': 6000}}

'''
# expire_after_seconds = None
# for index_name,v in index_dict:
#     if index_name =='utime_1':
#         expire_after_seconds = v['expireAfterSeconds']
#
#
# print(col.list_indexes())



