#coding:utf-8
# @Time    : 2018/5/10
# @Author  : xiaopeng
# @Site    : boxueshuyuan
# @File    : test_zxp.py
# @Software: PyCharm
import timeit
from line_profiler import LineProfiler
import random
import redis
# import profile

#第一个
# def fun():
#     ''''dddd
#     sss
#     '''
#     j = 0
#     for i in range(1000):
#         j += 1
#
# print(timeit.timeit('fun', 'from __main__ import fun',number=10000))
# print(timeit.timeit())
#
# numbers = [random.randint(1,100) for i in range(1000)]
# lp = LineProfiler()
# lp_wrapper = lp(fun)
# lp_wrapper()
# lp.print_stats()

#第二个:

# b = []
# def A(p=[], d={'a':4}):
#     x = {'a':3}
#     print(p)
# A.xx = 2
# a = A([1])
# # b = A()
# print(dir(A))
# print(A.func_defaults)
# print(A.func_dict)
# print(A.__dict__)
#
# class B(object):
#     x = {'a':3}
#     def __new__(cls, *args, **kwargs):
#         dicts = dir(cls)
#         print(dicts)
#     def __init__(self):
#         self.y = {'d':6}
#
#     def hello(self):
#         pass

# b1 = B()
# b2 = B()
# b1.y['x'] = 9
# print(b1.y)
# print(b2.y)

# a = {'a':1}
# b = 1
# def dd():
#     global b
#     global a
#     b =2
#     a['a'] = 2
# dd()
# print(a,b)
# # b.x = 4
# print(B.__dict__)
# print(b.__dict__)
# print('-'*20)
# print(b.__class__.__dict__)

#第三个
r = redis.Redis(host='10.10.180.145', db=15)
# r.incr(name='dddd', amount=20)
# r.zincrby('dddd', 'd', amount=20)
# r.zincrby('dddd', 'e', amount=20)
print(r.zrange("list_hotel_holiday_20180523", 0, 2, withscores=True))
print(r.zrange("dddd", 0, -1, withscores=False))
print(r.zrank('dddd', 'd'))