#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2016年12月1日

@author: dujun
'''
import functools
import tornado


# tornado start
def admin_authenticated(func):
    admins = {'admin': 'Mia0ji123'}

    @functools.wraps(func)
    def wrapper(*args, **kw):
        if len(args) > 0 and isinstance(args[0], tornado.web.RequestHandler):
            handler = args[0]
            if handler.get_arguments('user') and handler.get_arguments('pwd'):
                user = handler.get_arguments('user')[0]
                pwd = handler.get_arguments('pwd')[0]
                if admins.get(user, None) != pwd:
                    raise tornado.web.HTTPError(403, 'admin_authenticated requested')
                else:
                    r = func(*args, **kw)
                    return r
            else:
                raise tornado.web.HTTPError(403, 'admin_authenticated requested')
        else:
            # 非tornado请求
            raise Exception("this func is not tornado.web.RequestHandler's")

    return wrapper


def query_authenticated(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        if len(args) > 0 and isinstance(args[0], tornado.web.RequestHandler):
            # handler = args[0]
            # TODO 认证、请求限制 
            if False:
                raise tornado.web.HTTPError(403, 'admin_authenticated requested')
            else:
                r = func(*args, **kw)
                return r
        else:
            # 非tornado请求
            raise Exception("this func is not tornado.web.RequestHandler's")

    return wrapper
