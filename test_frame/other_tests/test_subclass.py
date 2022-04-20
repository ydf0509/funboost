class A:
    pass


class B(A):
    pass

class C(B):
    pass

print(issubclass(C, A))