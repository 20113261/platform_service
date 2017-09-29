#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/27 下午8:21
# @Author  : Hou Rong
# @Site    :
# @File    : TestElong.py
# @Software: PyCharm
# 342781aef5b8304572841c549e321d3e
import unittest
import json
from proj.my_lib.new_hotel_parser.expedia_parser import expedia_parser
from mioji.common.ufile_handler import download_file


def test_expedia_parser(page):
    return expedia_parser(page,
                        url='',
                        other_info={'source_id': 'test', 'city_id': 'test'}
                        )


class TestElong(unittest.TestCase):
    def test_address(self):
        cases = ['2c91813ffb981500801d080cd2cbb56d']
        results = [('Royal Road 23,Grand Bay',)]
        for case, res in zip(cases, results):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_expedia_parser(j_data['data'])
            self.assertTupleEqual((result.address,), res)

    def test_description(self):
        cases = ['2c91813ffb981500801d080cd2cbb56d']
        results = [
            ('地点::这家Grande Bay酒店依傍着海滩，距离Blue Water Diving Center 1.7 公里、大湾海滩 2.5 公里。而且，卡诺涅尔海滩和蒙舒瓦西海滩距离酒店不到 2 公里。|_|酒店服务设施::在海洋别墅酒店的私人白沙海滩晒晒太阳、在提供全面服务的 SPA 中心享受服务，或者尝试浮潜。|_|客房设施::所有 40 间客房设有冰箱和泡咖啡用具等便利设施，以及免费 WiFi和阳台。卫星电视、迷你吧和电话是店方为客人提供的其他设施/服务。',),
        ]
        for case, res in zip(cases, results):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_expedia_parser(j_data['data'])
            self.assertTupleEqual((result.description,), res)

    def test_accepted_cards(self):
        cases = ['2c91813ffb981500801d080cd2cbb56d']
        results = [('万事达卡|大莱卡|美国运通卡|维萨卡',)]
        for case, res in zip(cases, results):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_expedia_parser(j_data['data'])
            self.assertTupleEqual((result.accepted_cards,), res)

    def test_service(self):
        cases = ['2c91813ffb981500801d080cd2cbb56d']
        results = [
            ('酒店设施：保姆/儿童看护（收费）,机场交通（收费）,房间总数 - 40,楼层数 - 2,24 小时前台服务,烧烤炉,商务中心,礼宾服务,干洗/洗衣服务,快速办理入住,快速退房,全套 SPA 服务|互联网：保姆/儿童看护（收费）,机场交通（收费）,房间总数 - 40,楼层数 - 2,24 小时前台服务,烧烤炉,商务中心,礼宾服务,干洗/洗衣服务,快速办理入住,快速退房,全套 SPA 服务|停车：保姆/儿童看护（收费）,机场交通（收费）,房间总数 - 40,楼层数 - 2,24 小时前台服务,烧烤炉,商务中心,礼宾服务,干洗/洗衣服务,快速办理入住,快速退房,全套 SPA 服务',),
        ]
        for case, res in zip(cases, results):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_expedia_parser(j_data['data'])
            self.assertTupleEqual((result.service,), res)




if __name__ == '__main__':
    unittest.main()
