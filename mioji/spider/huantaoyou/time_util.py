#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

# TODO, retrive times for view ticket: match hh:mm and compare lists
# TODO, retrive times for tour_ticket
# TODO, retrive times for play_ticket
# TODO, retrive times for activity_ticket  太难了
moment_pattern = re.compile(r'\d\d:\d\d')  # match for hh:mm
moment_pattern_bak = re.compile(r'\d\d*?:\d\d')  # match for hh:mm
time_range = re.compile(r'\d\d:\d\d-\d\d:\d\d')  # match for hh:mm
time_range_bak = re.compile(r'\d\d*?:\d\d-\d\d*?:\d\d')  # match for hh:mm
min_pattern = re.compile(u'\u5206\u949f')
hour_pattern = re.compile(u'\u5c0f\u65f6')
digtal_pattern = re.compile(r'[0-9]*\.?[0-9]+')


class TimeNotFoundError(Exception):
    pass


def compare_time_str(t1, t2):
    h1, m1 = t1.split(':')
    h2, m2 = t2.split(':')
    return int(h2) * 3600 + int(m2) * 60 > int(h1) * 3600 + int(m1) * 60

def sub_time_str(t1, t2):
    h1, m1 = t1.split(':')
    h2, m2 = t2.split(':')
    sub_time = (int(h2) * 3600 + int(m2) * 60) - (int(h1) * 3600 + int(m1) * 60)
    if sub_time > 0:
	return sub_time
    return -sub_time

def match_time_view(input_str):
    '''
    @input: str
    @desc: find all time part that formatted as HH:MM
    @return earliest and lastest time str
    '''
    if input_str is None:
        return None, None  # 默认值？
    result = moment_pattern_bak.findall(input_str)
    if not result:  # 如果匹配到
    	result = moment_pattern.findall(input_str)
    if result:  # 如果匹配到
        matched = result
        if len(matched) == 1:
            return matched[0], matched[0]
        else:  # 多项 进行排序
            matched.sort(cmp=compare_time_str)
            return matched[0], matched[-1]
    return None, None  # 默认值？



def get_time_for_view_ticket(input_str):
    t1, t2 = match_time_view(input_str)
    dur = sub_time_str(t1, t2)
    ret = []
    if t1 == t2:
        t2 = None
    if t1 and t2 and compare_time_str(t1, t2):
        ret.append({'t': t1, 'dur': dur})
    elif t1 and t2 and not compare_time_str(t1, t2):
        ret.append({'t': t2, 'dur': dur})
    elif t1:
        ret.append({'t': t1, 'dur': dur})
    elif t2:
        ret.append({'t': t2, 'dur': dur})
    else:
        ret.append({'t': '', 'dur': dur})
    return ret 


def get_dur_for_view_ticket(input_str):
    # mongo 返回的全部为 unicode
    if min_pattern.search(input_str):
        offset = 60
    elif hour_pattern.search(input_str):
        offset = 3600
    else:
	return -3 
        #raise TimeNotFoundError(input_str)
    digital = digtal_pattern.search(input_str)
    if digital:
        return int(float(digital.group()) * offset)
    raise TimeNotFoundError(input_str)


def match_time_play(input_str):
    ret = []
    if input_str is None:
        return ret
    # match range
    result = time_range.findall(input_str)
    if result:
        for r in result:
            ret.append(r.split('-')[0])
            ret.append(r.split('-')[1])
        return ret
    result = moment_pattern.findall(input_str)
    if result:
        for r in result:
            ret.append(r)
        return ret
    raise TimeNotFoundError(input_str)

def get_time_for_play_tickets(perform_time, perfrom_period):
    # match 2 format, time_range and mement_pattern
    ret = []
    sessions = match_time_play(perform_time)
    if len(sessions) == 1:
        dur = get_dur_for_view_ticket(perfrom_period)
        ret.append({'t': sessions[0], 'dur': dur})
	return ret
    for i in range(0, len(sessions), 2):
        ret.append({'t': sessions[i], 'dur': sub_time_str(sessions[i],sessions[i+1])})
    return ret


def match_time_activity(input_str):
    '''
    @input: str
    @desc: find all time part that formatted as HH:MM
    @return earliest and lastest time str
    '''
    result = moment_pattern.findall(input_str)
    if result:  # 如果匹配到
        matched = result
        if len(matched) == 1:
            return matched[0], matched[0]
        else:  # 多项 进行排序
            matched.sort(cmp=compare_time_str)
            return matched[0], matched[-1]
    raise TimeNotFoundError(input_str)


def get_time_for_activity_ticket(consumer_remind):
    ret = []
    dur = -3 
    keys = ['visit_period', 'consumer_period', 'repast_period']
    for key in keys:
        val = consumer_remind.get(key, None)
        if val:
            dur = get_dur_for_view_ticket(val)
            break

    keys = ['transfer_time', 'depart_time', 'take_ticket_time', 'open_time',
            'ride_time', 'visit_time', 'repast_time']
    for key in keys:
        val = consumer_remind.get(key, None)
        if val:
            try:
                t1, _ = match_time_activity(val)
                ret.append({'t': t1, 'dur': dur})
                break
            except TimeNotFoundError:
                pass
    '''
    t2 = consumer_remind.get('open_time', None)
    try:
        _, t2 = match_time_activity(t2)
        if t2:
            ret.append({'t': t2, 'dur': dur})
    except:
        pass
    '''
    return ret


def get_time_for_tour_ticket(t1, dur):
    ret = []
    '''
    if dur:
        dur = get_dur_for_view_ticket(dur)
    else:
        dur = -3
    '''
    try:
        t1, t2 = match_time_view(t1)
        if t1 == t2:
            t2 = None
	if t1 and t2 and compare_time_str(t1, t2):
            ret.append({'t': t1, 'dur': dur})
        elif t1 and t2 and not compare_time_str(t1, t2):
            ret.append({'t': t2, 'dur': dur})
	elif t1:
            ret.append({'t': t1, 'dur': dur})
	elif t2:
            ret.append({'t': t2, 'dur': dur})
	else:
            ret.append({'t': '', 'dur': dur})
    except Exception,e:
	print e	
    return ret

if __name__ == '__main__':
    #print get_time_for_view_ticket("|8:30登船。5小时。")
    #print get_time_for_play_tickets('<div>3月7日-4月30日：</div><div>10:15-16:15(每天)。</div><div><br></div><div>5月1日-6月19日：</div><div>09:30-17:00(周日到周四)。</div><div>09:30-20:00(周五到周六)。</div><div><br></div><div>6月20日-9月1日：</div><div>09:30-20:00(周日到周四)。</div><div>09:30-21:30(周五到周六)。</div><div><br></div><div>9月2日-10月12日：</div><div>09:30-17:00(周日到周四)。</div><div>09:30-20:00(周五到周六)。</div><div><br></div><div>10月13日-10月31日：</div><div>09:30-17:00(每天)。</div><div>11月1日-12月31日：</div><div>10:15-17:15(每天)。</div>', u"约90分钟")
    print get_time_for_play_tickets('19:00。','4小时')
    #print get_time_for_activity_ticket(None, "桑拿&amp;汗蒸房：白天 05:00-21:00，夜间 21:00-05:00。", None)
    #print get_time_for_tour_ticket("8:30", "5小时。")
