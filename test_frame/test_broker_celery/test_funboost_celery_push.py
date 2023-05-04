

from test_celery_beat_consume import f_beat,f_beat2


for i in range(100):
    f_beat.push(i, i + 1)
    res2 = f_beat2.push(i, i * 2)
    print(type(res2),res2.get())