#!/usr/bin/env python
# -*- coding: utf-8 -*-

from proj.my_lib.Common.Utils import Coordinate

import datetime
import json

class Column(object):
    def __init__(self, typ, default):
        self._typ = typ
        self._default = default
        self._value = None

    def judgement_type(self, value):
        return self._typ.type(value)

    def __str__(self):
        return str(self._default) if self._value is None else str(self._value)



class BaseType(object):
    def __init__(self, length):
        if type(length) is not int:
            raise TypeError('%s must be int' % str(length))

    def __str__(self):
        return self.__class__.__name__

class String(BaseType):
    def type(self, value):
        return type(value) is str

class Integer(BaseType):
    def type(self, value):
        return type(value) is int

class Datetime(BaseType):
    def type(self, value):
        return isinstance(value, datetime.datetime)

class Text(BaseType):
    def type(self, value):
        return type(value) is str

class Map(BaseType):
    def type(self, value):
        return isinstance(value, Coordinate)

class JSON(BaseType):
    def type(self, value):
        try:
            json.loads(value)
            return True
        except Exception as e:
            return False


if __name__ == '__main__':
    c = Column(Integer(), datetime.datetime.now())
    c.default = datetime.datetime.now()
    print c