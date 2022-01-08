from nb_log import get_logger
import time
from concurrent.futures import ProcessPoolExecutor
logger = get_logger('test_nb_log_conccreent',is_add_stream_handler=True,log_filename='test_nb_log_conccreent35.log')

from auto_run_on_remote import run_current_script_on_remote

def f(x):
    for i in range(200):
        time.sleep(0.3)
        logger.warning(f'{x} {i}')

# logger.warning('aaaaa')
if __name__ == '__main__':
    run_current_script_on_remote()
    # 200万条 45秒

    pool = ProcessPoolExecutor(10)
    print('start')
    for i in range(2):
        pool.submit(f,i)
    pool.shutdown()
    print('end')