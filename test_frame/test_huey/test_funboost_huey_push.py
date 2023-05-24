

from test_funboost_huey_consume import f1,f2
for i in range(10):
    f1.push(i, i + 1)
    f2.push(i)

