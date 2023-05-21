import argparse
import sys
import nb_log
import dramatiq
from dramatiq.cli import main, make_argument_parser
import requests

print(dramatiq.get_broker())
from dramatiq.brokers.redis import RedisBroker

redis_broker = RedisBroker(host="127.0.0.1", port=6379)
dramatiq.set_broker(redis_broker)

print(dramatiq.get_broker().actor_options)



@dramatiq.actor
def count_words(url):
    response = requests.get(url)
    count = len(response.text.split(" "))
    print(f"There are {count} words at {url!r}.")


@dramatiq.actor(queue_name='f2q')
def f2(url):
    response = requests.get(url)
    count = len(response.text.split(" "))
    print(f"There are {count} words at {url!r}.")

@dramatiq.actor(queue_name='f3q')
def f3(url):
    response = requests.get(url)
    count = len(response.text.split(" "))
    print(f"There are {count} words at {url!r}.")



if __name__ == '__main__':

    count_words.send("http://www.baidu.com")
    # p = make_argument_parser()
    p = argparse.ArgumentParser()
    pa =p.parse_args()
    px= make_argument_parser()
    pa.broker = 'test_dramatiq_raw'
    pa.modules = []
    pa.processes = 1
    pa.threads=8
    pa.path = '.'
    pa.queues=None
    pa.log_file=None
    pa.skip_logging = False
    pa.use_spawn = False
    pa.forks = []
    pa.worker_shutdown_timeout = 600000
    pa.verbose = 0
    pa.pid_file = None
    print(31)
    print(32, pa)

    main(pa)


'''
Namespace(broker='test_dramatiq_raw', modules=[], processes=1, threads=8, path='.', queues=None, pid_file=None, log_file=None, skip_logging=False, use_spawn=False, forks=[], worker_shutdown_timeout=600000, verbose=0)
python -m dramatiq test_dramatiq_raw -p 1
'''