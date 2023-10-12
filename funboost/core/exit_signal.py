import os
import signal


# noinspection PyProtectedMember,PyUnusedLocal
def _interrupt_signal_handler(signalx, framex):
    print('你按了 Ctrl+C  。 You pressed Ctrl+C!  结束程序！')
    # sys.exit(0)
    # noinspection PyUnresolvedReferences
    os._exit(0)  # os._exit才能更强力的迅速终止python，sys.exit只能退出主线程。


def set_interrupt_signal_handler():
    ''' 有的包里面自己写了 signal.signal，导致这个_interrupt_signal_handler函数不能生效'''
    signal.signal(signal.SIGINT, _interrupt_signal_handler)



'''
用户自己导入 from funboost.utils.ctrl_c_end import ctrl_c_recv 函数加到文件最末尾.
'''
