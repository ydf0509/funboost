from test_dramatiq_raw import count_words,f2,f3

count_words.send("http://www.baidu.com")


f2.send("http://www.sina.com")

f3.send("http://www.sina.com")