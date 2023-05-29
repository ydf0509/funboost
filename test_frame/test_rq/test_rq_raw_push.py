from main import q

from test_frame.test_rq.test_rq_raw import count_words_at_url

result = q.enqueue(
             count_words_at_url, 'https://www.twle.cn')


