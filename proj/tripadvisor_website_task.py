#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/17 下午5:34
# @Author  : Hou Rong
# @Site    : 
# @File    : tripadvisor_website_task.py
# @Software: PyCharm
import pymongo
import pymongo.errors

from .my_lib.BaseTask import BaseTask
from my_lib.Common.Browser import MySession
from .celery import app

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['TripAdvisor']['website']


@app.task(bind=True, base=BaseTask, max_retries=5, rate_limit='3/s')
def website_url_task(self, source_id, before_website_url, **kwargs):
    try:
        with MySession() as session:
            page = session.get(before_website_url, verify=False)
            website_url = page.url
            try:
                collections.save({
                    'source_id': source_id,
                    'website': website_url
                })
            except pymongo.errors.DuplicateKeyError as exc:
                print str(exc)
    except Exception:
        self.retry(countdown=20)


if __name__ == '__main__':
    pass
