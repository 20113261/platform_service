#coding:utf-8
# @Time    : 2018/5/19
# @Author  : xiaopeng
# @Site    : boxueshuyuan
# @File    : _test_zxp_2.py
# @Software: PyCharm

# !/usr/bin/python
# coding :utf-8
from mioji.common.spider import Spider
import importlib
import inspect
from pkgutil import extend_path, iter_modules, walk_packages, get_data
from mioji.spider import IHGHotel
from mioji import spider

#test1
aa = {'a':1}
bb = {'aa': aa}
aa['b'] = 2

#test2
# class SpiderZxp(Spider):
#     source_type = 'ctripHotel'
#
#     targets = {
#         # 例行需指定数据版本：InsertHotel_room4
#         'room': {'version': 'InsertHotel_room3'},
#     }
#
#     def __init__(self):
#         super(SpiderZxp, self).__init__()
#
#     def targets_request(self):
#         pass
#
#     def parse_room(self):
#         pass

#test3
def predicate(value):
    if inspect.isclass(value) and value.__module__.endswith('_spider'):
        return True

#test4
def test_pkgutil():
    print(spider.__path__)
    __path__ = iter_modules(spider.__path__, spider.__name__ + ".")
    for i in __path__:
        print(i)
    __path__ = walk_packages(spider.__path__, spider.__name__ + ".")
        # walk_packages('test_ser_2_mioji.spider.IHGHotel', '')
    for i in __path__:
        print(i)
    __path__ = iter_modules(IHGHotel.__path__, IHGHotel.__name__ + ".")
    print get_data(IHGHotel.__name__, 'holiday_hotel_spider.py')


def test_spiderzxp():
    module = importlib.import_module('.spider.IHGHotel.holiday_hotel_spider', 'mioji')
    for i in inspect.getmembers(module, predicate=predicate):
        print(i)
    a = module.IhgHotelSpider()


def monkey_patch(name, bases, dct):
    assert len(bases) == 1
    base = bases[0]
    for name, value in dct.iteritems():
        if name not in ('__module__', '__metaclass__'):
            setattr(base, name, value)
    return base


class A(object):
    def a(self):
        print 'i am A object'


class PatchA(A):
    __metaclass__ = monkey_patch

    def patcha_method(self):
        print 'this is a method patched for class A'


def main():
    test_pkgutil()
    # test_spiderzxp()
    # pa = PatchA()
    # pa.patcha_method()
    # pa.a()
    # print dir(pa)
    # print dir(PatchA)


if __name__ == '__main__':
    main()