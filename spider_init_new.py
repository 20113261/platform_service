#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/6/20 上午10:20
# @Author  : Hou Rong
# @Site    : 
# @File    : spider_init_new.py
# @Software: PyCharm

# coding=utf-8
# coding='utf8'
import re

from proj.tasks import get_comment


def add_target(task_url, miaoji_id, **kwargs):
    res1 = get_comment.delay(task_url, 'zhCN', miaoji_id, **kwargs)
    res2 = get_comment.delay(task_url, 'en', miaoji_id, **kwargs)
    return res1, res2


d_pattern = re.compile('-d(\d+)')

if __name__ == '__main__':
    # from proj.hotel_static_tasks import hotel_static_base_data
    #
    # print hotel_static_base_data('7ededbc01f00e0463f064e6ca9f8235f', 'hotel_base_data_170612')

    from proj.suggestion_task import ctrip_suggestion_task

    ctrip_suggestion_task('10001', '巴黎', task_id='test')
