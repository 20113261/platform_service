#!/usr/bin/python
# -*- coding: UTF-8 -*-


'''
Created on 2018年03月09日

@author: 15596663161@163.com
'''

import json
from mioji.common.logger import logger
# from mioji.common.class_common import Room
from mioji.common.func_log import func_time_logger
from collections import defaultdict
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()


class Tag(object):
    def __init__(self):
        # 星级
        self.star = 'star'
        # 位置 景点、商业区、行政区
        self.district = 'district'
        # 酒店品牌
        self.chains = 'chains'
        # 酒店设施
        self.facilities = 'facilities'
        # 酒店评分
        self.grade = 'grade'
        # 酒店类型
        self.hoteltype = 'hoteltype'
        # 早餐
        self.mealplan = 'mealplan'
        # 房型偏好
        self.twin_double = 'twin_double'

    # def items(self):
    #     results = []
    #     for k, v in self.__dict__.items():
    #         results.append((k, str(v).decode("UTF-8")))
    #     return results

def parse_hotel_list_tag(req,dom,city_id):
    result = defaultdict(list)
    result['city_id'] = city_id
    # 星级
    # class_tag = dict()
    # 位置 景点、商业区、行政区
    # district_tag = dict()
    # 酒店品牌
    # chains_tag = dict()
    # 酒店设施
    # facilities_tag = dict()
    # 酒店评分
    # review_tag = dict()
    # 酒店类型
    # hoteltype_tag = dict()
    # 早餐
    # 房型偏好


    try:
        total_tag_dom = dom.get_element_by_id("filterbox_options")
        print 'total_tag_dom-----------'
        print total_tag_dom
    except:
        try:
            total_tag_dom = dom.find_class('filterbox_options_content')[0]
        except:
            print "页面改版，需要调整解析逻辑"
            print req['resp'].url
            # with open('fail_url.txt','a') as f:
            #     f.write(city_id+'\n')
            #     f.write(req['resp'].url+'\n')
            return result

    # 星级div
    class_div_dom = None
    try:
        class_div_dom = total_tag_dom.get_element_by_id('filter_class')
    except:
        pass
    if class_div_dom is not None:
        for class_options_dom in class_div_dom.find_class('filteroptions'):
            class_options_list = class_options_dom.getchildren()
            for class_options in class_options_list:
                try:
                    # print class_options.attrib['data-id']
                    data_id = class_options.attrib['data-id']
                    temp_title = class_options.find_class('filter_label')[0].text.strip()
                    if 0 == len(temp_title):
                        temp_title = class_options.text_content().strip().split('\n')[0]
                    # print temp_title
                    result['hotel_star'].append({"key":temp_title,"id":data_id})
                except:
                    pass

    # 位置div
    district_div_dom = None
    try:
        district_div_dom = total_tag_dom.get_element_by_id('filter_district')
    except:
        pass
    if district_div_dom is not None:
        free_districts_dict = {"name":"景点/商业区","tag_list":[]}
        political_districts_dict = {"name":"行政区","tag_list":[]}
        for district_options_dom in district_div_dom.find_class('filteroptions'):
            # 景点/商业区 free_districts
            for free_districts_div in district_options_dom.find_class('free_districts'):
                free_districts_options_list = free_districts_div.getchildren()
                for free_districts_option in free_districts_options_list:
                    try:
                        # print free_districts_option.attrib['data-id']
                        data_id = free_districts_option.attrib['data-id']
                        temp_title = free_districts_option.find_class('filter_label')[0].text.strip()
                        if 0 == len(temp_title):
                            temp_title = free_districts_option.text_content().strip().split('\n')[0]
                        # print temp_title
                        free_districts_dict['tag_list'].append({"name":temp_title,"id":data_id})
                    except:
                        pass
            result["position"].append(free_districts_dict)
            # 行政区
            for political_districts_div in district_options_dom.find_class('political_districts'):
                political_districts_options_list = political_districts_div.getchildren()
                for political_districts_option in political_districts_options_list:
                    try:
                        # print political_districts_option.attrib['data-id']
                        data_id = political_districts_option.attrib['data-id']
                        temp_title = political_districts_option.find_class('filter_label')[0].text.strip()
                        if 0 == len(temp_title):
                            temp_title = political_districts_option.text_content().strip().split('\n')[0]
                        # print temp_title
                        political_districts_dict['tag_list'].append({"name":temp_title,"id":data_id})
                    except:
                        pass
            result["position"].append(political_districts_dict)

    # 地标 landmark
    landmark_div_dom = None
    try:
        landmark_div_dom = total_tag_dom.get_element_by_id('filter_popular_nearby_landmarks')
    except:
        pass
    if landmark_div_dom is not None:
        landmark_dict = {"name":"地标","tag_list":[]}
        for landmark_options_dom in landmark_div_dom.find_class('filteroptions'):
            landmark_options_list = landmark_options_dom.getchildren()
            for landmark_options in landmark_options_list:
                try:
                    data_id = landmark_options.attrib['data-id']
                    temp_title = landmark_options.find_class('filter_label')[0].text.strip()
                    if 0 == len(temp_title):
                        temp_title = landmark_options.text_content().strip().split('\n')[0]
                    landmark_dict['tag_list'].append({"name":temp_title,"id":data_id})
                except:
                    pass
            result['position'].append(landmark_dict)

    # 酒店品牌div
    chains_div_dom = None
    try:
        chains_div_dom = total_tag_dom.get_element_by_id('filter_chains')
    except:
        pass
    if chains_div_dom is not None:
        chains_dict = {"name":"品牌","tag_list":[]}
        for chains_options_dom in chains_div_dom.find_class('filteroptions'):
            chains_options_list =  chains_options_dom.getchildren()
            for chains_options in chains_options_list:
                try:
                    # print chains_options.attrib['data-id']
                    data_id = chains_options.attrib['data-id']
                    temp_title = chains_options.find_class('filter_label')[0].text.strip()
                    if 0 == len(temp_title):
                        temp_title = chains_options.text_content().strip().split('\n')[0]
                    # print temp_title
                    chains_dict['tag_list'].append({"segment_name":temp_title,"segment_info":data_id})
                except:
                    pass
        result["others_info"].append(chains_dict)

    # 酒店设施
    facilities_div_dom = None
    try:
        facilities_div_dom = total_tag_dom.get_element_by_id('filter_facilities')
    except:
        pass
    if facilities_div_dom is not None:
        facilities_dict = {"name":"设施服务","tag_list":[]}
        for facilities_options_dom in facilities_div_dom.find_class('filteroptions'):
            facilities_options_list = facilities_options_dom.getchildren()
            for facilities_options in facilities_options_list:
                try:
                    # print facilities_options.attrib['data-id']
                    data_id = facilities_options.attrib['data-id']
                    temp_title = facilities_options.find_class('filter_label')[0].text.strip()
                    if 0 == len(temp_title):
                        temp_title = facilities_options.text_content().strip().split('\n')[0]
                    # print temp_title
                    facilities_dict["tag_list"].append({"segment_name":temp_title,"segment_info":data_id})
                except:
                    pass
        result["others_info"].append(facilities_dict)

    # 酒店评分
    review_div_dom = None
    try:
        review_div_dom = total_tag_dom.get_element_by_id('filter_review')
    except:
        pass
    if review_div_dom is not None:
        review_dict = {"name":"酒店评分","tag_list":[]}
        for review_options_dom in review_div_dom.find_class('filteroptions'):
            review_options_list = review_options_dom.getchildren()
            for review_options in review_options_list:
                try:
                    # print review_options.attrib['data-id']
                    data_id = review_options.attrib['data-id']
                    temp_title = review_options.find_class('filter_label')[0].text.strip()
                    if 0 == len(temp_title):
                        temp_title = review_options.text_content().strip().split('\n')[0]
                    # print temp_title
                    review_dict['tag_list'].append({"segment_name":temp_title,"segment_info":data_id})
                except:
                    pass
        result["others_info"].append(review_dict)

    # 酒店类型
    hoteltype_div_dom = None
    try:
        hoteltype_div_dom = total_tag_dom.get_element_by_id('filter_hoteltype')
    except:
        pass
    if hoteltype_div_dom is not None:
        hoteltype_dict = {"name":"酒店类型","tag_list":[]}
        for hoteltype_options_dom in hoteltype_div_dom.find_class('filteroptions'):
            hoteltype_options_list = hoteltype_options_dom.getchildren()
            for hoteltype_options in hoteltype_options_list:
                try:
                    # print hoteltype_options.attrib['data-id']
                    data_id = hoteltype_options.attrib['data-id']
                    temp_title = hoteltype_options.find_class('filter_label')[0].text.strip()
                    if 0 == len(temp_title):
                        temp_title = hoteltype_options.text_content().strip().split('\n')[0]
                    # print temp_title
                    hoteltype_dict['tag_list'].append({"segment_name":temp_title,"segment_info":data_id})
                except:
                    pass
        result["others_info"].append(hoteltype_dict)

    # 早餐
    mealplan_div_dom = None
    try:
        mealplan_div_dom = total_tag_dom.get_element_by_id('filter_mealplan')
    except:
        pass
    if mealplan_div_dom is not None:
        for mealplan_options_dom in mealplan_div_dom.find_class('filteroptions'):
            mealplan_options_list = mealplan_options_dom.getchildren()
            for mealplan_options in mealplan_options_list:
                try:
                    # print mealplan_options.attrib['data-id']
                    data_id = mealplan_options.attrib['data-id']
                    temp_title = mealplan_options.find_class('filter_label')[0].text.strip()
                    if 0 == len(temp_title):
                        temp_title = mealplan_options.text_content().strip().split('\n')[0]
                    # print temp_title
                    result["breakfast"].append({"name":temp_title,"id":data_id})
                except:
                    pass

    # 房型偏好
    twin_double_div_dom = None
    try:
        twin_double_div_dom = total_tag_dom.get_element_by_id('filter_twin_double')
    except:
        pass
    if twin_double_div_dom is not None:
        twin_double_dict = {"name":"床型","tag_list":[]}
        for twin_double_options_dom in twin_double_div_dom.find_class('filteroptions'):
            twin_double_options_list = twin_double_options_dom.getchildren()
            for twin_double_options in twin_double_options_list:
                try:
                    # print twin_double_options.attrib['data-id']
                    data_id = twin_double_options.attrib['data-id']
                    temp_title = twin_double_options.find_class('filter_label')[0].text.strip()
                    if 0 == len(temp_title):
                        temp_title = twin_double_options.text_content().strip().split('\n')[0]
                    # print temp_title
                    twin_double_dict['tag_list'].append({"segment_name":temp_title,"segment_info":data_id})
                except:
                    pass

    # 排序:
    # order: distance_from_landmark 距离市中心
    #        price 价格排序
    #        popularity 推荐排序
    # json_result = json.dumps(result)
    return [result]


