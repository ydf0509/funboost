




class A():
    x =1
    y=3

class B(A):
    x=2


class Mixinx():
    x=3

MyCode = type("MyCode", (B, ),{})

print(MyCode().x)

print(B.mro())

print(B.__mro__)