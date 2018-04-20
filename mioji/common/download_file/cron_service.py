#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/25 下午12:35
# @Author  : Hou Rong
# @Site    :
# @File    : script_crond_monitor.py
# @Software: PyCharm
import functools
import inspect
import traceback

import requests

from apscheduler.schedulers.blocking import BlockingScheduler
from download_img import download_pic
from logger import get_logger
from delete_file import delete_already_scanned_file

logger = get_logger('cron_task_monitor')
SEND_TO = ['hourong@mioji.com', "luwanning@mioji.com"]


def send_email(title, mail_info, mail_list, want_send_html=False):
    try:
        mail_list = ';'.join(mail_list)
        data = {
            'mailto': mail_list,
            'content': mail_info,
            'title': title,
        }
        if want_send_html:
            data['mail_type'] = 'html'
        requests.post('http://10.10.150.16:9000/sendmail', data=data)
    except Exception as e:
        logger.exception(msg="[send email error]", exc_info=e)
        return False
    return True


def on_exc_send_email(func):
    @functools.wraps(func)
    def wrapper():
        func_name = func.__name__
        try:
            func_file = inspect.getabsfile(func)
        except Exception as exc:
            logger.exception(msg="[get file exc]", exc_info=exc)
            try:
                func_file = inspect.getfile(func)
            except Exception as exc:
                logger.exception(msg="[get local file exc]", exc_info=exc)
                func_file = 'may be local func: {}'.format(func_name)
        try:
            logger.debug('[异常监控]统计及数据入库例行 执行 [file: {}][func: {}]'.format(func_file, func_name))
            func()
            logger.debug('[异常监控]统计及数据入库例行 执行完成 [file: {}][func: {}]'.format(func_file, func_name))
        except Exception as exc:
            logger.exception(msg="[run func or send email exc]", exc_info=exc)
            send_email('[异常监控]统计及数据入库例行 异常',
                       '[file: {}][func: {}] \n\n\n {}'.format(func_file, func_name, traceback.format_exc()), SEND_TO)

    return wrapper


schedule = BlockingScheduler()
schedule.add_job(on_exc_send_email(download_pic), 'cron', second='*/30', id='download_pic')
schedule.add_job(on_exc_send_email(delete_already_scanned_file), 'cron', hour='*/2', id='delete_already_scanned_file',
                 max_instances=1)

if __name__ == '__main__':
    schedule.start()
