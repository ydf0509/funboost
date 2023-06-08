from test_rq_raw import q

from test_rq_raw import count_words_at_url

# result = q.enqueue(
#              count_words_at_url, 'https://www.twle.cn')


count_words_at_url.delay('https://www.twle.cn')


count_words_at_url.delay('https://www.sina.cn')

