#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月12日

@author: hourong
'''

from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import budgetair_flight_lib
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW


class BudgetairFlightSpider(Spider):
    # 抓取目标 如城市列表、酒店列表 等对象
    source_type = 'budgetairFlight'

    # 数据目标 如城市、酒店数据、酒店房型数据等。
    #   一个抓取目标可以对应多个，数据对象。
    #   一个抓取数据对应一个解析方法 parse_xxx 如：parse_hotelList_hotel，parse_hotelList_room
    targets = {
        # 例行需指定数据版本：InsertNewFlight
        'Flight': {'version': 'InsertNewFlight'},
    }

    # 对应多个老原爬虫
    old_spider_tag = {
        'budgetairFlight': {'required': ['Flight']}
    }

    def targets_request(self):
        self.task_info = budgetair_flight_lib.parse_task(self.task.content)
        task_url = 'https://api.budgetair.co.uk/fares/cid-800712c2-9d35-432e-b2b3-b1ab58c44c51/groupedresults?adt={adult_nu}&inf={infant_nu}&chd={child_nu}&cls=Y&out0_dep={dept_id}&out0_arr={dest_id}&out0_date={dept_day}'.format(
            **self.task_info)

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_Flight)
        def api_page():
            return {'req':
                {
                    'url': task_url,
                    'headers': {
                        'accept': '*/*',
                        'accept-encoding': 'gzip, deflate, sdch, br',
                        'accept-language': 'zh-CN,zh;q=0.8,en;q=0.6',
                        'origin': 'https://www.budgetair.co.uk',
                    }
                },
                'data': {
                    'content_type': 'json'
                },
            }

        return [api_page]

    def parse_Flight(self, req, data):
        tickets = budgetair_flight_lib.parser_page(root=data, **self.task_info)
        return tickets


if __name__ == '__main__':
    from mioji.common.task_info import Task

    content = 'BCN&PEK&20170701&3&E&24_0.5_10&1_0_1'
    task = Task('budgetairFlight', content)

    spider = BudgetairFlightSpider()
    spider.task = task
    print spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
