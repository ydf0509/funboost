from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass


@dataclass(order=True)
class Model1:
    a = 1
    b = 2
    poop = ThreadPoolExecutor(20)
    asdf = 34

m1 = Model1(p)


