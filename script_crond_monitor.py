#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/25 下午12:35
# @Author  : Hou Rong
# @Site    : 
# @File    : script_crond_monitor.py
# @Software: PyCharm





# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/6 下午9:01
# @Author  : Hou Rong
# @Site    :
# @File    : rabbitmq_watcher.py
# @Software: PyCharm
import sys

sys.path.append('/root/data/lib')
from apscheduler.schedulers.blocking import BlockingScheduler
from script.download_img import download_pic

schedule = BlockingScheduler()
schedule.add_job(download_pic, 'cron', second='*/40', id='download_pic')

if __name__ == '__main__':
    schedule.start()
