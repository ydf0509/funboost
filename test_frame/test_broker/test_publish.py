import time

from test_frame.test_broker.test_consume import f

# f.clear()
# for i in range(1000000):
#     # time.sleep(0.2)
#     if i == 0:
#         print(time.strftime("%H:%M:%S"), '发布第一条')
#     if i == 99999:
#         print(time.strftime("%H:%M:%S"), '发布第100000条')
#     f.push(i, i * 2)

if __name__ == '__main__':
    f.multi_process_pub_params_list([{'x':i,'y':2*i} for i in range(100000)],process_num=5)