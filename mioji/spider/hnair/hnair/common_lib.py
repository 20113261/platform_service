#!/usr/bin/env python
# -*- coding: utf-8 -*-



"""
这个文件包含了飞机类型的一些公用的class
"""
# E经济舱、B商务舱、F头等舱、P超级经济舱
query_cabin_dict = {'E': 'y_s', 'B': 'c', 'F': 'f', 'P': 'y_s'}


def seat_type_to_queryparam(seat_type):
    return query_cabin_dict.get(seat_type, 'Y_S')


def process_ages(passenger_count, age_info=None):
    # 处理乘客信息
    # 返回 adult_count, child_count, infant
    if age_info is None:
        return passenger_count, 0, 0
    age_info_dict = {
        'adult': 0,
        'child_count': 0,
        'infant_count': 0,
    }
    ages = age_info.split('_')
    if len(ages) == 1 and ages[0] == '-1':
        return passenger_count, 0, 0
    for age in ages:
        judge_age(age, age_info_dict)

    test_count = age_info_dict['adult'] + age_info_dict['child_count'] + age_info_dict['infant_count']
    assert passenger_count == test_count
    return age_info_dict['adult'], age_info_dict['child_count'], age_info_dict['infant_count']


def judge_age(age, age_info_dict):
    # 成人  1人 儿童(2-12岁) 1人 婴儿(14天-2岁) 1人
    if age == '-1':
        age_info_dict['adult'] += 1
        return
    age_int = int(age)
    if age_int < 12:
        # 需要判定是否有婴儿
        if 0 < age_int <= 2:
            age_info_dict['infant_count'] += 1
        else:
            age_info_dict['child_count'] += 1
    elif 12 <= age_int:
        age_info_dict['adult'] += 1


def test_(age_info, count):
    result = {'Quantity': process_ages(count, age_info)[0], 'ChildQuantity': process_ages(count, age_info)[1],
              'InfantQuantity': process_ages(count, age_info)[2]}
    print result


# def process_passenger_info(adults='1', child=[], child_count=0, has_infant=False):
#     '''生成乘客信息'''
#     # passengers=adults:1,children:1[3],seniors:0,infantinlap:N  乘客信息的
#     infant_inlap = 'N'
#     if has_infant:
#         infant_inlap = 'Y'
#     child_str = ','.join(child)
#     ret = 'passengers=adults:%s,seniors:0,infantinlap:%s' % (
#         adults, infant_inlap
#     )
#     if child:
#         ret += ',children:%s[%s]' % (child_count, child_str)
#     return ret


if __name__ == '__main__':
    a = 2
    b = '-1'
    test_(b, a)


