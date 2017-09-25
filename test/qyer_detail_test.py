#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/25 下午10:30
# @Author  : Hou Rong
# @Site    : 
# @File    : qyer_detail_test.py
# @Software: PyCharm
from proj.qyer_poi_tasks import qyer_poi_task

if __name__ == '__main__':
    qyer_poi_task(target_url='http://place.qyer.com/poi/V2EJalFiBzVTYw/', city_id='TEST',
                  task_name='detail_total_qyer_test')
