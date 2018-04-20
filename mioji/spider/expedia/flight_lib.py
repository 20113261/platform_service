#!/usr/bin/env python
# -*- coding: utf-8 -*-



"""
这个文件包含了飞机类型的一些公用的class
"""


def process_ages(passenger_count, age_info=None):
    # 处理乘客信息
    # 返回 adult_count, child_age_list, child_count, has_infant
    if age_info is None:
        return passenger_count, [], 0, False
    age_info_dict = {
        'adult': 0,
        'senior': 0,
        'child': [],
        'child_count': 0,
        'has_infant': False,
    }
    for age in age_info.split('_'):
        judge_age(age, age_info_dict)

    test_count = age_info_dict['adult'] + len(age_info_dict['child']) + age_info_dict['senior']
    assert passenger_count == test_count
    return age_info_dict['adult'], age_info_dict['child'], age_info_dict['child_count'], age_info_dict['has_infant']


def judge_age(age, age_info_dict):
    # expedia 判定18+都为成人
    if age == '-1':
        age_info_dict['adult'] += 1
        return
    age_int = int(age)
    if age_int < 18:
        # 需要判定是否有婴儿
        age_info_dict['child'].append(age)
        age_info_dict['child_count'] += 1
        #age_info_dict['child_count'] = 0
        if not age_info_dict['has_infant']:
            age_info_dict['has_infant'] = is_infant(age_int)
    elif 18 <= age_int:
        age_info_dict['adult'] += 1


def is_infant(age):
    if 0 <= age < 2:
        return True
    return False


def process_passenger_info(adults='1', child=[], child_count=0, has_infant=False):
    '''生成乘客信息'''
    # passengers=adults:1,children:1[3],seniors:0,infantinlap:N  乘客信息的
    infant_inlap = 'N'
    if has_infant:
        infant_inlap = 'Y'
    #child_str = ','.join(child)
    child_str = ';'.join(child)
    ret = 'passengers=adults:%s,seniors:0,infantinlap:%s' % (
        adults, infant_inlap
    )
    if child:
        ret += ',children:%s[%s]' % (child_count, child_str)
    else:
        ret = 'passengers=children:0,adults:%s,seniors:0,infantinlap:%s' % (
            adults, infant_inlap
        )
        pass
    return ret


if __name__ == '__main__':
    a = 2
    b = '-1_1'
    adults, child, child_count, has_infant = process_ages(a, b)
    print(process_passenger_info(adults, child, child_count, has_infant))


