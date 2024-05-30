#
#
# # def get_child_custom_attr(child_cls:type,):
# #     __dict = child_cls.__dict__
#
# def merge_cls(cls1:type,cls2:type):
#     class Cls(cls2):
#         pass
#     for k,v in cls1.__dict__.items():
#         if k.startswith('__') and k.endswith('__'):
#             continue
#         print(k,v)
#         setattr(Cls,k,v)
#     return Cls
#
#
# if __name__ == '__main__':
#     class Parent:
#         attr1=1
#         def method_from_parent(self):
#             print('method_from_parent')
#
#         def method_from_parent2(self):
#             print('method_from_parent2')
#
#
#     class Child(Parent):
#         attr1=2
#         attr2=22
#
#         def method_from_parent2(self):
#             print('method_from_parent2chile')
#         def method_from_child(self:Parent):
#             print('method_from_child')
#
#     class Child2(Parent,Parent):
#         attr1 = 3
#
#     class Child2b(Child2):
#         attr1 = '2b'
#
#
#     class Child2New(Child2b,Child):
#         pass
#
#
#     print(Child2().method_from_parent2())
#     print(Child2New().method_from_parent2())
#
#
#
