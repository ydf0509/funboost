from funboost import ActiveCousumerProcessInfoGetter



print(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_queue_name('test_queue'))
print(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_ip())
print(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_ip('10.0.195.220'))

print(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_queue_name())
print(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_ip())