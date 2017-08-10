#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/12 下午4:46
# @Author  : Hou Rong
# @Site    :
# @File    : tripadvisor_list_tasks.py
# @Software: PyCharm
import pymongo
import urlparse
import traceback

from proj.my_lib.task_module.task_func import update_task
from .my_lib.BaseTask import BaseTask
from my_lib.Common.Browser import MySession
from pyquery import PyQuery
from .celery import app

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['HotelList']['TripAdvisor']


def init_header(source_city_id, page_index):
    ctx = dict()
    ctx['page_index'] = page_index
    ctx['source_city_id'] = source_city_id
    ctx["url"] = "https://cn.tripadvisor.com/Hotels-g{0}".format(source_city_id) \
        if page_index == 0 else "https://cn.tripadvisor.com/Hotels-g{0}-oa{1}".format(source_city_id,
                                                                                      (page_index - 1) * 30)

    ctx["headers"] = {
        "Host": "cn.tripadvisor.com",
        "Origin": "https://cn.tripadvisor.com",
        "Referer": "https://cn.tripadvisor.com/Hotels-g{0}".format(source_city_id),
    }
    return ctx


@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='3/s')
def list_page_task(self, ctx, city_id, **kwargs):
    self.task_source = 'TripAdvisor'
    self.task_type = 'HotelList'
    with MySession() as session:
        try:
            session.headers.update(ctx['headers'])
            resp = session.get(ctx['url'])
            jq = PyQuery(resp.text)

            # 爬取详情页
            doc_a_href = jq(".property_title")

            for each in doc_a_href.items():
                # 详情页 id
                detail_id = each.attr("id").split('_')[-1]
                # 详情页链接
                detail_url = urlparse.urljoin(resp.url, each.attr("href"))
                collections.save({
                    'city_id': city_id,
                    'source_id': detail_id,
                    'source_url': detail_url,
                    'task_id': kwargs['task_id'],
                    'page_index': ctx['page_index']
                })

            # 爬取下一页，如果不是第一页，这部分不进行
            if ctx['page_index'] == 0:
                total_page = jq(".pageNum.last").attr("data-page-number")
                for i in range(1, int(total_page) + 1):
                    # 用对方的 city_id 生成抓取信息
                    ctx = init_header(ctx['source_city_id'], i)

                    # 分发异步任务
                    app.send_task('proj.tripadvisor_list_tasks.list_page_task',
                                  args=(ctx, city_id,),
                                  kwargs=kwargs,
                                  queue='tripadvisor_list_tasks',
                                  routing_key='tripadvisor_list_tasks')

            update_task(kwargs['task_id'])
        except Exception as exc:
            session.update_proxy('23')
            self.retry(exc=traceback.format_exc(exc))


if __name__ == '__main__':
    pass
