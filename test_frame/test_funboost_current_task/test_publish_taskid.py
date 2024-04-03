import time

from test_current_task import f,aiof


for i in range(100):
    time.sleep(1)
    f.publish({'a':i,'b':i*2})
    aiof.publish({'a': i, 'b': i * 2})