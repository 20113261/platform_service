#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading
from collections import defaultdict


class TSCounter(object):
    def __init__(self, val=0):
        self.val = val

    @property
    def val(self):
        with threading.Lock():
            return self.__val

    @val.setter
    def val(self, val):
        with threading.Lock():
            self.__val = val

    def __str__(self):
        return str(self.val)

    def __add__(self, val):
        with threading.Lock():
            self.val += val

    def __sub__(self, val):
        with threading.Lock():
            self.val -= val


class UnFinishedSet():
    def __init__(self):
        self.set = set()
        self.dict = defaultdict(lambda: 0)
        self.un_handled_set = set()

    def add(self, val):
        with threading.Lock():
            self.dict[val] += 1

            if self.dict[val] > 1:
                self.set.add(val)

    def __contains__(self, val):
        with threading.Lock():
            return val in self.set

    def left_id(self):
        return list(self.set)

    def un_handled(self, val):
        with threading.Lock():
            self.un_handled_set.add(val)


# An exception that need to skip this value
class SkipException(Exception):
    pass
