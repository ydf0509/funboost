from funboost import ActiveCousumerProcessInfoGetter
from test_frame.my.test_consume import f2


print(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_queue_name(f2.queue_name))
print(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_ip())
print(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_ip('10.0.195.220'))

print(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_queue_name())
print(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_ip())