#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/15 上午10:16
# @Author  : Hou Rong
# @Site    : ${SITE}
# @File    : TaskResponse.py
# @Software: PyCharm


class TaskResponse(object):
    def __init__(self, **kwargs):
        self.source = kwargs.get('source', '')
        self.type = kwargs.get('type', '')
        self.error_code = kwargs.get('error_code', 103)
