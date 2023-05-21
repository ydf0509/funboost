from test_dramatiq_raw import count_words

count_words.send("http://www.baidu.com")