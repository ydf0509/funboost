
from redis import Redis
from rq import Queue



q = Queue(connection=Redis())

import requests

def count_words_at_url(url):
    resp = requests.get(url)
    return resp.text






if __name__ == '__main__':
    '''
    rq workor
    '''
