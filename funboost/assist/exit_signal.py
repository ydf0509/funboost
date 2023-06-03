import signal


# noinspection PyProtectedMember,PyUnusedLocal
def _interrupt_signal_handler(signalx, framex):
    print('你按了 Ctrl+C  。 You pressed Ctrl+C!  结束程序！')
    # sys.exit(0)
    # noinspection PyUnresolvedReferences
    os._exit(0)  # os._exit才能更强力的迅速终止python，sys.exit只能退出主线程。


signal.signal(signal.SIGINT, _interrupt_signal_handler)
