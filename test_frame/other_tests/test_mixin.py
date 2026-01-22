

class A:
    def __init__(self):
        self.a = 1
        self.custom_init()
        
    def custom_init(self):
        pass
    
    
class B(A):
    def custom_init(self):
        self.b = 2
        print('B custom_init')
        


class MixinC(A):
    def custom_init(self):
        super().custom_init()
        self.c = 3
        print('MixinC custom_init')
        
        
class D(MixinC, B,A):
    pass

print(D().__dict__)
