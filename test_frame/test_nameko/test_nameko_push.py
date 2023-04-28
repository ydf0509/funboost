from test_funboost_nameko import f, f2

for i in range(100):
    print(f.push(i, b=i + 1))
    print(f2.push(x=i, y=i * 2))
