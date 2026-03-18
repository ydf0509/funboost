

class A:
    def  __init__(self):
        print('A __init__')
        self.custom_init()

    def custom_init(self):
        pass


class B(A):
    def custom_init(self):
        print('B custom_init')


class MixinC(A):
    def custom_init(self):
        super().custom_init()
        print('MixinC custom_init')

class D(MixinC, B,A):
    pass

d = D()

