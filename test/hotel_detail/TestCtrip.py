#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/27 下午8:31
# @Author  : Hou Rong
# @Site    : 
# @File    : TestHotels.py
# @Software: PyCharm
import unittest
import json
from proj.my_lib.new_hotel_parser.ctrip_parser import ctrip_parser
from mioji.common.ufile_handler import download_file


def test_ctrip_parser(page):
    return ctrip_parser(page,
                        url='',
                        other_info={'source_id': 'test', 'city_id': 'test'}
                        )


class TestCtrip(unittest.TestCase):
    def test_name(self):
        cases = ['d80436af0e5cc301b52ebd6dc0f0ef52']
        results = [(u'比比度假旅馆', u"Bibi's Hideaway")]
        for case, res in zip(cases, results):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_ctrip_parser(j_data['data'])
            self.assertTupleEqual((result.hotel_name, result.hotel_name_en), res)

    def test_service(self):
        cases = ['d80436af0e5cc301b52ebd6dc0f0ef52']
        results = ['网络连接::有可无线上网的公共区域|停车场::停车场|通用设施::吸烟区|活动设施::烧烤|服务项目::翻译服务|行李寄存|儿童看护|24小时前台服务|接机服务']
        for case, res in zip(cases, results):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_ctrip_parser(j_data['data'])
            self.assertEqual(result.service, res)

    def test_desc(self):
        cases = ['516a5403a6773c16e9988d3efc81062c']
        results = [
            '2001年开业，2014年装修，共有91间房。坐落于沃尔马的金沙套房水疗度假村(SandsSuitesResort&Spa)，会让您在毛里求斯拥有别样的体验，开展一段难忘的旅行。旅客们会发现海豚湾、TamarinaGolfClub和塔马兰公共海滩距离酒店都不远。酒店占尽地理之宜，ShotzNightClub、双体船畅游海豚湾和Sundivers离此都很近。客房内的所有设施都是经过精心的考虑和安排，包括房内保险箱、液晶电视机和房间内高速上网，满足您入住需求的同时又能增添家的温馨感。除此之外，配备有吹风机的浴室是您消除一天疲劳的好地方。酒店内的西餐厅供应特色菜肴，来满足旅客的需求。在空闲的时候，去酒吧喝杯饮品放松一下是不错的选择。如果旅客想在自己的房间舒适的用餐，酒店可提供客房服务。酒店周边的美食也等待着您的探索，ZubExpressRestaurant（东南亚菜）会供应一流的推荐美味Beefcurry，LeDix-neuf（西餐）和Paul&Virginie（西餐）也会让您大吃一惊，定会对两家的WokfriedNoodleswithBeeforChicken和grilledlobster赞不绝口。相信按摩室周到的服务和室外游泳池一流的设施，会让您拥有别样的体验。酒店的会议厅和商务中心将热情的服务与专业的素质完美地结合在一起。品质保证的礼宾服务，让您真正体验宾至如归的享受。免费停车场会对入住酒店的客人开放。']
        for case, res in zip(cases, results):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_ctrip_parser(j_data['data'])
            self.assertEqual(result.description, res)

    def test_cityId(self):
        cases = ['71cdba64fdcaa92bfeb8ba3d6530ec76']
        results = ['tokyo228']
        for case, res in zip(cases, results):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_ctrip_parser(j_data['data'])
            self.assertEqual(result.source_city_id, res)
    # def test_pay_method(self):
    #     cases = ['d80436af0e5cc301b52ebd6dc0f0ef52', '516a5403a6773c16e9988d3efc81062c']
    #     results = [u'在线付|到店付|礼品卡支付', u'在线付|到店付|礼品卡支付']
    #     for case, res in zip(cases, results):
    #         page = download_file(case)
    #         j_data = json.loads(page)
    #         result = test_ctrip_parser(j_data['data'])
    #         self.assertEqual(result.pay_method, res)

    def test_accept_card(self):
        cases = ['d80436af0e5cc301b52ebd6dc0f0ef52', '516a5403a6773c16e9988d3efc81062c']
        results = ['master|visa', 'master|visa|amex|diners club']
        for case, res in zip(cases, results):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_ctrip_parser(j_data['data'])
            self.assertEqual(result.accepted_cards, res)


if __name__ == '__main__':
    unittest.main()
