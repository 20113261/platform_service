#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2016年11月8日

@author: dujun
'''

TASK_ERROR = 12
PROXY_NONE = 21
PROXY_INVALID = 22
PROXY_FORBIDDEN = 23
REQ_ERROR = 2
DATA_FORMAT_ERROR = 3

PARSE_ERROR = 27
DATA_NONE = 24
UNKNOWN_ERROR = 25
EMPTY_TICKET = 29

STORAGE_ERROR = 31
STORAGE_UNKNOWN_ERROR = 32
RABBITMQ_ERROR = 33
MYSQL_ERROR = 34
RABBITMQ_MYSQL_ERROR = 35

FLIP_WARRING = 36

API_ERROR = 89
API_NOT_ALLOWED = 90
API_EMPTY_DATA = 92


class ParserException(Exception):
    TASK_ERROR = 12
    PROXY_NONE = 21
    PROXY_INVALID = 22
    PROXY_FORBIDDEN = 23
    REQ_ERROR = 2
    DATA_FORMAT_ERROR = 3

    PARSE_ERROR = 27
    DATA_NONE = 24
    UNKNOWN_ERROR = 25
    EMPTY_TICKET = 29

    STORAGE_ERROR = 31
    FLIP_WARRING = 36

    API_ERROR = 89
    API_NOT_ALLOWED = 90
    API_EMPTY_DATA = 92

    def __init__(self, parser_error_code, msg=''):
        self.code = parser_error_code
        self.msg = msg

    def __str__(self):
        return 'code: %d, msg:%s' % (self.code, self.msg)

    def __repr__(self):
        return self.__str__()


if __name__ == '__main__':

    try:
        raise ParserException(22, 'error msg')
    except ParserException, e:
        import traceback

        print traceback.format_exc()
        print("parser error: {0}".format(e))
    except Exception, e:
        print str(e)
