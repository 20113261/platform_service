#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年2月16日

@author: dujun
'''

import functools, traceback

class SafeResult(object):
    
    def __init__(self, result, args, kw, error=None,):
        self.result = result
        self.error = error
        self.args = args
        self.kw = kw
        print 'kw', kw
    
    def isok(self):
        return not self.error
    
    def __str__(self, *args, **kwargs):
        return '<SafeResult> result={0},error={1},args={2},kw={3}'.format(self.result, self.error, self.args, self.kw)

def except_wrap(fun):
    
    if fun.__dict__.get('mioji.aop_utils.logger', False):
        return fun
    @functools.wraps(fun)
    def _wrap(*args, **kw):
        try:
            result = fun(*args, **kw)
            return SafeResult(result, args, kw)
        except Exception, e:
            return SafeResult(None, args, kw, error=str(e))
        
    return _wrap

@except_wrap
def test(a, c='ss'):
    return 1

if __name__ == '__main__':
    print test('ss')
