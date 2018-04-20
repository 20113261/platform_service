#coding:utf-8
import inspect, re

# def varname(p):
#     m = None
#     for line in inspect.getframeinfo(inspect.currentframe().f_back)[3]:
#         m = re.search(r'\bvarname\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)', line)
#     if m:
#         return m.group(1)
#
# a = {'a':2}
# vname = lambda v,nms: [ vn for vn in nms if id(v)==id(nms[vn])][0]
# print(vname(a, locals()))

# aaa = '23asa'
# bbb = 'kjljl2'
# def get_variable_name(variable):
#     loc = locals()
#     print loc
#     for key in loc:
#         if loc[key] == variable:
#             return key
# print get_variable_name(aaa)
#
# aaa = '23asa'
# bbb = 'kjljl2'
# lst = [aaa,bbb,aaa]
# value = lst[1]
# loc = locals()
# def get_variable_name(variable):
#     print loc
#     for key in loc:
#         if loc[key] == variable:
#             return key
# print get_variable_name(value)
#
# aaa = '23asa'
# bbb = 'kjljl2'
# loc = locals()
# def get_variable_name(variable):
#     print loc
#     for key in loc:
#         if loc[key] == variable:
#             return key
# print get_variable_name(aaa)

# def get_variable_name(x):
#     for k,v in locals().items():
#         if v is x:
#             return k
# def print_var(x):
#     print(get_variable_name(x),'=',x)
#
# a = 1
# b = 1
# print_var(a)
# print_var(b)

class A(object):
    class_var = 1

    def __init__(self):
        self.name = 'xy'
        self.age = 2

    @property
    def num(self):
        return self.age + 10

    def fun(self): pass

    def static_f(): pass

    def class_f(cls): pass


if __name__ == '__main__':  # 主程序
    a = A()
    print a.__dict__  # {'age': 2, 'name': 'xy'}   实例中的__dict__属性
    print A.__dict__
    print dir(A)