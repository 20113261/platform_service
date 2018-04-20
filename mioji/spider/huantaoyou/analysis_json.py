#!/usr/bin/env python
# coding: utf-8

import sys
import json
import traceback
import datetime
from copy import deepcopy
from consumer_remind import get_cn_consumer
from mongo import get_ref_poi, get_mioji_poi
from util import SkipException
from time_util import get_time_for_view_ticket, get_time_for_tour_ticket, \
    get_time_for_play_tickets, get_time_for_activity_ticket, TimeNotFoundError
reload(sys)
sys.setdefaultencoding("utf-8")


"""
说明：
几种类型的API解析函数都写在这个文件中，
函数传进来的值都为网页传回来的数据的json
"""

def calTime(time,day):
    time = datetime.datetime(int(time.split('-')[0]),int(time.split('-')[1]),int(time.split('-')[2]))
    new_time = datetime.timedelta(days=day) + time
    new_time_str = new_time.strftime('%Y-%m-%d')
    return new_time_str

def join_keyword(keyword, list):
    """
    提取一个形状如[{'a': 1, 'b': 2}, {'a': 2, 'b': 3}] 返回拼接好的字符串
    :param keyword: 你所要提取的keyword 形如 'a' list: 待提取的list
    :return: 拼接好的字符串 形如 '1|2'
    """
    temp = []
    for i in list:
        temp.append(i[keyword])
    return '|'.join(str(d) for d in temp)


def get_ticket_desc(rep):
    val_list = []

    try:  # 票券类型
        if rep['verification']['name']:
            val_list.append('票券类型:' + rep['verification']['name'])
    except Exception:
        pass

    try:
        if rep['consumer_remind']['take_ticket_time']:
            val_list.append(
                '取票时间:' + rep['consumer_remind']['take_ticket_time'])
    except Exception:
        pass

    try:
        if rep['consumer_remind']['take_ticket_address']:
            val_list.append(
                '取票地点:' + rep['consumer_remind']['take_ticket_address'])
    except Exception:
        pass

    try:
        if rep['verification']['remark']:
            val_list.append(rep['verification']['remark'])
    except Exception:
        pass
    return '|'.join(val_list)

    # a = ['verification', 'consumer_remind', 'consumer_remind', 'verification']
    # b = ['name', 'take_ticket_time', 'take_ticket_address', 'remark']
    # c = ['票券类型:', '取票时间:', '取票地点:', '']
    # for x, y, z in zip(a, b, c):
    #     try:
    #         if rep[a][b]:
    #             val_list.append(c + rep[a][b])
    #     except:
    #         continue


def get_info(rep):
    recommend = []
    for i in rep['taste']:
        if 'recommend' in i:
            if rep['taste'][i] is not None:
                recommend.append(rep['taste'][i])
            else:
                continue
    if recommend:
        recommend = '|'.join(recommend)
    else:
        recommend = ''

    age_min = min(join_keyword('age_min', rep.get('skulist')).split('|'))
    age_max = max(join_keyword('age_max', rep.get('skulist')).split('|'))
    age_min = '0' if age_min == '0' else age_min
    age_max = '0' if age_max == '0' else age_max
    age_range = '年龄限制 ({0} - {1})'.format(age_min, age_max)
    if age_range == '(年龄限制  -  )':
        age_range = '暂无信息'
    if age_min == age_max and age_min == '0':
        age_range = '无限制'

    CPXX = []
    for i in rep['trait']:
        CPXX.append('title: {0}|'.format(i.get('title', None)))
        CPXX.append('description: {0}|'.format(i.get('description', None)))
        CPXX.append('image_url: {0}|'.format(i.get('image_url', None)))
    CPXX = ''.join(CPXX)

    GDXX = []
    for inf in rep['consumer_remind']:
        GDXX.append(str(inf) + ':' + str(rep['consumer_remind'][inf]))
    GDXX = '|'.join(GDXX)
    GDXX = get_cn_consumer(GDXX)

    ret = {}
    ret['TJKD'] = rep.get('sub_title', None)
    ret['FWYY'] = rep.get('service_language', '英语')
    ret['PQSYSM'] = get_ticket_desc(rep)

    if rep.get('consumer_terminal', None):
        ret['JDJS'] = '景点图片: {0}|景点介绍: {1}'.format(
            rep['consumer_terminal']['image_url'], rep['consumer_terminal']['remark'])
        ret['CKXC'] = rep['consumer_terminal']['line']
    else:
        ret['JDJS'] = None
        ret['CKXC'] = None
    ret['YCAP'] = None
    ret['ZSAP'] = None

    ret['FYBH'] = rep.get('prebook_remind', {}).get('contain_fee', None)
    ret['FYNBH'] = rep.get('prebook_remind', {}).get('not_contain_fee', None)
    ret['SYRQ'] = rep.get('prebook_remind').get('age_range') if rep.get('prebook_remind', {}).get(
        'age_range', None) else age_range

    ret['GMXZ'] = '最多预定人数: {0}|最少预订人数: {1}|提前预定天数: {2}'.format(
        '无限制' if str(rep.get('skulist')[0].get('max_reserve', None)) == '0' else rep.get('skulist')[0].get(
            'max_reserve', None),
        '无限制' if str(rep.get('skulist')[0].get('min_reserve', None)) == '0' else rep.get('skulist')[0].get(
            'min_reserve', None),
        int(rep.get('book_day', '1')) + 1 if str(rep.get('book_hour', None)) != '0' or str(
            rep.get('book_minute', None)) != '0' else rep.get('book_day', '1'))

    ret['CPXX'] = '{0}{1}{2}{3}{4}'.format(
        rep.get('taste', {}).get('title', '') + '|',
        rep.get('taste', {}).get('description', '') + '|',
        recommend + '|',
        rep.get('taste', {}).get('image_url', '') + '||',
        CPXX)

    ret['GDXX'] = GDXX
    ret['TGSM'] = rep.get('policy', {}).get('description', None)
    ret['ZYSX'] = rep.get('prebook_remind', {}).get('other', None)
    return ret


def handle_poi(rep):
    try:
        poi = rep['consumer_terminal']['consumer_terminal_id']
        return get_ref_poi(poi)
    except Exception:
        # TODO 生成假数据后，删掉
        raise SkipException('No poi relation')
        # return {
        #     'relation': "POI NOT FOUND",
        #     'city_id': 'POI NOT FOUND',
        #
        #         }


def get_date(rep):
    ticket = rep['skulist'][0]
    try:
        date = ticket.get('schedule', [{}])[0].get('type', None)
    except:
        date = None
    if str(date) == '0':
        date = ticket.get('schedule', [{}])[0].get('date', None)
    elif str(date) == '1':
        date = ticket.get('schedule', [{}])[0].get(
            'start_time', None) + '~' + ticket.get('schedule', [{}])[0].get('end_time', None)
    else:
        date = '暂无数据'
    return date


def get_times(rep, ticket_type):
    times = []

    if ticket_type == 'view_ticket':
        try:
            open_time = rep['consumer_remind']['open_time']
            times = get_time_for_view_ticket(open_time)
        except (TimeNotFoundError, KeyError, Exception):
            pass
    elif ticket_type == 'play_ticket':
        try:
            perform_time = rep['consumer_remind']['perform_time']
            perfrom_period = rep['consumer_remind']['perform_period']
            times = get_time_for_play_tickets(perform_time, perfrom_period)
        except (TimeNotFoundError, KeyError, Exception):
            pass
    elif ticket_type == 'activity_ticket':
        try:
            times = get_time_for_activity_ticket(rep['consumer_remind'])
        except (TimeNotFoundError, Exception):
            pass
    elif ticket_type == 'tour_ticket':
        try:
            t1 = rep['consumer_remind'].get('transfer_time', '|') + \
                 rep['consumer_remind'].get('depart_time', '|') + \
                 rep['consumer_remind'].get('visit_time', '|')
            # t1 = min time, t2 = max time, if t1 = t2, keep t1
            if '半日' in rep['title']:
                dur = -1
            else:
                dur -2
            '''
                dur = rep['consumer_remind'].get('visit_period', '|') + \
                    rep['consumer_remind'].get('consumer_period', '|')
            '''
            times = get_time_for_tour_ticket(t1, dur)
        except (TimeNotFoundError, Exception):
            pass
    return times


def get_pres(rep):
    book_day = rep.get('book_day', 0)
    book_minute = rep.get('book_minute', 0)
    book_hour = rep.get('book_hour', 0)
    book_pre = None
    if str(rep.get('book_day', '暂无数据')) != '0' and str(rep.get('book_hour', '暂无数据')) != '0':
        try:
            book_pre = (int(book_day) * 24 + int(book_hour)) * 3600 + int(book_minute) * 60
        except Exception as e:
            book_pre = 'book_day不为数字型'
    enter_pre = 0
    return book_pre, enter_pre


def get_base(rep):
    ret = {}
    #a_poi = handle_poi(rep)
    #ret['ref_poi'] = a_poi['relation']
    ret['name'] = rep.get('title', None)
    ret['ename'] = None
    # ret['city_id'] = None if (rep.get('consumer_terminal', {}) and
    #                           rep['consumer_terminal'].get('city_id', 0)) else rep['consumer_terminal']['city_id']
    #ret['city_id'] = a_poi['city_id']
    ret['addr'] = rep.get('consumer_terminal', {}).get(
        'chinese_name', None)  # 活动地址
    #ret['map_info'] = get_mioji_poi(a_poi['relation'])['coordinate']
    ret['first_img'] = rep.get('surface', None)
    ret['img_list'] = rep.get('imglist', [])
    ret['date'] = get_date(rep)
    # 不去times 要从返回值里面取类型
    ret['book_pre'], ret['enter_pre'] = get_pres(rep)
    try:
        if int(rep['skulist'][0]['isShuttle']) == 1:
            ret['jiesong_type'] = '2'
    except:
        pass
    if 'jiesong_type' not in ret:
        ret['jiesong_type'] = '0'
    coord = 'NULL'
    if rep['consumer_terminal']:
        coord = str(rep['consumer_terminal']['longitude']) + ',' + str(rep['consumer_terminal']['latitude'])
    jiesong_poi = []
    if rep["consumer_remind"].get("transfer_address", "") != "" and rep["consumer_remind"].get("transfer_time", "") != "":
        jiesong_poi = [{
            "addr": "接送地址: {0}|接送时间:{1}".format(
                rep["consumer_remind"].get("transfer_address", "is null").replace("'","\""),
                rep["consumer_remind"].get("transfer_time", "is null")).replace("'", "\""),
            "coord": coord
        }]
    jiesong_poi_str = json.dumps(jiesong_poi, ensure_ascii=False)
    if jiesong_poi_str.find("is null"):
        jiesong_poi = []
    ret['id_3rd'] = str(rep['id'])
    return ret

def get_date_price(resp, sku_id):
    skulist = resp["skulist"]
    sku = skulist[sku_id]
    price = 9999999999999
    schedule = sku['schedule']
    for sched in schedule:
        if sched['price'] < price:
            price = sched['price']

    data_price = []
    t_open = {}
    t_open['f'] = sku['start_time']
    blackDateList = sku['blackDateList']
    t_open['t'] = sku['end_time']
    t_open['p'] = deepcopy(price)
    t_week = []
    week = {'Mon':1,'Tue':2,'Wed':3,'Thu':4,'Fri':5,'Sat':6,'Sun':7}
    if sku['schedule']:
        for day in sku['schedule'][0]['week']:
            t_week.append(week[day])
    t_open['w'] = t_week
    if blackDateList:
        for i in range(0, len(blackDateList)+1):
            if i < len(blackDateList):
                if i == 0:
                    t_open['f'] = sku['start_time']
                    t_open['t'] = calTime(blackDateList[i], -1)
                    t_open['w'] = t_week
                    t_open['p'] = deepcopy(price) #sku['schedule'][0]['price'] if sku['schedule'] else -1
                    data_price.append(deepcopy(t_open))
                elif i != len(blackDateList)-1 and calTime(blackDateList[i], 1) != blackDateList[i+1]:
                    t_open['f'] = calTime(blackDateList[i], 1)
                    t_open['t'] = calTime(blackDateList[i+1], -1)
                    t_open['w'] = t_week
                    t_open['p'] = deepcopy(price) #sku['schedule'][0]['price'] if sku['schedule'] else -1
                    data_price.append(deepcopy(t_open))
                else:
                    pass
            else:
                t_open['f'] = calTime(blackDateList[i-1], 1)
                t_open['t'] = sku['end_time']
                t_open['p'] = deepcopy(price) #sku['schedule'][0]['price'] if sku['schedule'] else -1
                t_open['w'] = t_week
                data_price.append(deepcopy(t_open))
    else:
        data_price.append(deepcopy(t_open))
    return data_price

def view_ticket_analysis(response_json):
    """
    目前只有 view_ticket 使用
    几个解析json的公有解析字段
    :param response_json: json
    :return: dict
    待做：几个解析类共同使用base_analysis，有差异的地方再分别解析，这里为了方便写成了分别解析，其实有很多的重复字段。
    """
    # TODO local_id
    rep = response_json['data']
    poi_mode = 16384
    tag = '门票'

    jiesong_type_flag = join_keyword('isShuttle', rep.get('skulist'))
    # if len(set(jiesong_type_flag.split('|'))) != 1:
    #     print 'error'  # 此处改为记录日志

    return_dict = get_base(rep)
    del return_dict['addr']
    return_dict['times'] = [{"dur": "", "t": ""}]
    return_dict['poi_mode'] = poi_mode
    return_dict['info'] = get_info(rep)
    return_dict['changeInfo'] = '退改名称: {0}|退改说明:{1}'.format(rep['policy'].get('title', 'is null'),rep['policy'].get('description', '无').replace('<ul>','').replace('</ul>','').replace('<li>','').replace('</li>','').replace('<br>','').replace('</br>','').replace('&nbsp;','').replace(' ',''))
    if return_dict['changeInfo'].find('is null') != -1:
        return_dict['changeInfo'] = ''
    return_dict['tag'] = tag
    return return_dict


def play_ticket_analysis(response_json):
    """
    需要增加一个判定pid
    判断返回参数中consumer_remind节点下是否含有perform_time、perform_period任意一个字段。若含有任意一个，则归纳为play_ticket类产品
    """
    rep = response_json['data']
    poi_mode = 32768
    tag = '演出赛事'

    coord = 'NULL'
    if rep['consumer_terminal']:
        coord = str(rep['consumer_terminal']['longitude']) + ',' + str(rep['consumer_terminal']['latitude'])
    jiesong_poi = []
    if rep["consumer_remind"].get("transfer_address", "") != "" and rep["consumer_remind"].get("transfer_time", "") != "":
        jiesong_poi = [{
            "addr": "接送地址: {0}|接送时间:{1}".format(
                rep["consumer_remind"].get("transfer_address", "is null").replace("'","\""),
                rep["consumer_remind"].get("transfer_time", "is null")).replace("'", "\""),
            "coord": coord
        }]
    jiesong_poi_str = json.dumps(jiesong_poi, ensure_ascii=False)
    if jiesong_poi_str.find("is null"):
        jiesong_poi = []
    jiesong_type_flag = join_keyword('isShuttle', rep.get('skulist'))
    # if len(set(jiesong_type_flag.split('|'))) != 1:
    #     print 'error'  # 此处改为记录日志

    return_dict = get_base(rep)
    #return_dict['times'] = get_times(rep, 'play_ticket')
    return_dict['times'] = [{"dur": "", "t": ""}]
    return_dict['poi_mode'] = poi_mode
    return_dict['jiesong_poi'] = jiesong_poi
    return_dict['info'] = get_info(rep)
    return_dict['changeInfo'] = '退改名称: {0}|退改说明:{1}'.format(rep['policy'].get('title', 'is null'),rep['policy'].get('description', '无').replace('<ul>','').replace('</ul>','').replace('<li>','').replace('</li>','').replace('<br>','').replace('</br>','').replace('&nbsp;','').replace(' ',''))
    if return_dict['changeInfo'].find('is null') != -1:
        return_dict['changeInfo'] = ''
    return_dict['tag'] = tag
    return return_dict


def activity_ticket_analysis(response_json):
    """
    需要增加一个判定pid
    判断返回参数中consumer_remind节点下是否含有perform_time、perform_period任意一个字段。若含有任意一个，则归纳为play_ticket类产品
    """
    rep = response_json['data']
    poi_mode = '65536'
    tag = '特色活动'

    coord = 'NULL'
    if rep['consumer_terminal']:
        coord = str(rep['consumer_terminal']['longitude']) + ',' + str(rep['consumer_terminal']['latitude'])
    jiesong_poi = []
    if rep["consumer_remind"].get("transfer_address", "") != "" and rep["consumer_remind"].get("transfer_time", "") != "":
        jiesong_poi = [{
            "addr": "接送地址: {0}|接送时间:{1}".format(
                rep["consumer_remind"].get("transfer_address", "is null").replace("'","\""),
                rep["consumer_remind"].get("transfer_time", "is null")).replace("'", "\""),
            "coord": coord
        }]
    jiesong_poi_str = json.dumps(jiesong_poi, ensure_ascii=False)
    if jiesong_poi_str.find("is null"):
        jiesong_poi = []
    # jiesong_type_flag = join_keyword('isShuttle', rep.get('skulist'))
    # if len(set(jiesong_type_flag.split('|'))) != 1:
    #     print 'error'  # 此处改为记录日志

    return_dict = get_base(rep)
    #return_dict['times'] = get_times(rep, 'activity_ticket')
    return_dict['times'] = [{"dur": "", "t": ""}]
    return_dict['poi_mode'] = poi_mode
    return_dict['jiesong_poi'] = jiesong_poi
    return_dict['changeInfo'] = '退改名称: {0}|退改说明:{1}'.format(rep['policy'].get('title', 'is null'),rep['policy'].get('description', '无').replace('<ul>','').replace('</ul>','').replace('<li>','').replace('</li>','').replace('<br>','').replace('</br>','').replace('&nbsp;','').replace(' ',''))
    if return_dict['changeInfo'].find('is null') != -1:
        return_dict['changeInfo'] = ''
    return_dict['info'] = get_info(rep)
    return_dict['tag'] = tag
    return return_dict


def tour_ticket_analysis(response_json):
    rep = response_json['data']
    if '半日' in rep['title']:
        poi_mode = '131072'
        tag = '半日游'
    else:
        poi_mode = '262144'
        tag = '一日游'

    # jiesong_type_flag = join_keyword('isShuttle', rep.get('skulist'))
    # if len(set(jiesong_type_flag.split('|'))) != 1:
    #     print 'error'  # 此处改为记录日志
    return_dict = get_base(rep)
    #return_dict['times'] = get_times(rep, 'tour_ticket')
    return_dict['times'] = [{"dur": "", "t": ""}]
    return_dict['info'] = get_info(rep)
    return_dict['changeInfo'] = '退改名称: {0}|退改说明:{1}'.format(rep['policy'].get('title', 'is null'),rep['policy'].get('description', '无').replace('<ul>','').replace('</ul>','').replace('<li>','').replace('</li>','').replace('<br>','').replace('</br>','').replace('&nbsp;','').replace(' ',''))
    if return_dict['changeInfo'].find('is null') != -1:
        return_dict['changeInfo'] = ''

    return_dict['poi_mode'] = poi_mode
    return_dict['tag'] = tag
    return return_dict


def tickets_fun_analysis(response_json, val_):
    """
    所有的产品都需要添加这一个解析过程
    :param reponse_json: 网页返回的json
    :return: dict
    """
    # print response_json
    return_ticket = []
    rep = response_json['data']
    # result_list = []
    skuslist = rep['skulist']
    # for ticket in skulist:   # 暂时就只要一张票
    sku_id = 0
    for skulist in skuslist:
        ticket = skulist
        result_dict = {}
        name = ticket.get('sell_name')
        ccy = 'CNY'
        ticket_3rd = str(ticket.get('id', -1))
        sell_code = ticket.get('sell_code', None)
        # TODO info 应该是一个list
        if sell_code.find('1adult1child') != -1:
            info = [{"type": 0, "num": 1}, {"type": 1, "num": 1}]
        elif sell_code.find('2adult1child') != -1:
            info = [{"type": 0, "num": 2}, {"type": 1, "num": 1}]
        elif sell_code.find("child") != -1:
            info = [{"type": 1, "num": 1}, ]
        elif sell_code.find('adult') != -1:
            info = [{"type": 0, "num": 1}, ]
        elif sell_code.find('2adult') != -1:
            info = [{"type": 0, "num": 2}, ]
        elif sell_code.find('youth') != -1:
            info = [{"type": 10, "num": 1}, ]
        elif sell_code.find('general') != -1:
            info = [{"type": 4, "num": 1}, ]
        elif sell_code.find('people_beginner') != -1:
            info = [{"type": 5, "num": 1}, ]
        elif sell_code.find('people_experienced') != -1:
            info = [{"type": 6, "num": 1}, ]
        elif sell_code.find('people_kid') != -1:
            info = [{"type": 7, "num": 1}, ]
        elif sell_code.find('people_pupil') != -1:
            info = [{"type": 8, "num": 1}, ]
        elif sell_code.find('people_student') != -1:
            info = [{"type": 9, "num": 1}, ]
        elif sell_code.find('people_infant') != -1:
            info = [{"type": 2, "num": 1}, ]
        elif sell_code.find("old") != -1:
            info = [{"type": 3, "num": 1}, ]
        else:
            info = [{"type": 0, "num": 1}, ]
        price = join_keyword('price', ticket.get('schedule', [{}]))
        price = price.split('|')
        price = [int(i) for i in price]
        price = min(price)

        # if sell_code.split(',')[0] == 'child':
        #     info = [
        #         {"type": 1, "num": 1},
        #     ]
        #
        # elif sell_code.split(',')[0] == 'old':
        #     info = [
        #         {"type": 3, "num": 1},
        #     ]
        #     price = join_keyword('price', ticket.get('schedule', [{}]))
        #     price = price.split('|')
        #     price = [int(i) for i in price]
        #     price = min(price)
        #
        # else:
        #     info = [
        #         {"type": 0, "num": 1},
        #     ]
        #     price = join_keyword('price', ticket.get('schedule', [{}]))
        #     price = price.split('|')
        #     price = [int(i) for i in price]
        #     price = min(price)
        #if not val_['activity_ticket']:
        #    return {}
        times = [{"dur": "", "t": ""}]
        date = get_date(rep)
        book_pre, enter_pre = get_pres(rep)
        max_ = '0' if str(ticket.get('max_reserve', None)
                          ) == '0' else ticket.get('max_reserve', None)
        min_ = '0' if str(ticket.get('min_reserve', None)
                          ) == '0' else ticket.get('min_reserve', None)
        agemin = '0' if str(ticket.get('age_min', None)
                            ) == '0' else ticket.get('age_min', None)
        agemax = '0' if str(ticket.get('age_max', None)
                            ) == '0' else ticket.get('age_max', None)
        return_dict = {}
        # return_dict['pid'] = val_['pid']
        return_dict['sid'] = 1  # 欢逃游 我们自己生产的
        return_dict['name'] = name
        return_dict['ccy'] = ccy
        return_dict['times'] = times
        return_dict['date'] = date
        return_dict['book_pre'] = book_pre
        return_dict['enter_pre'] = enter_pre
        return_dict['max'] = max_
        return_dict['min'] = min_
        return_dict['changeInfo'] = '退改名称: {0}|退改说明:{1}'.format(rep['policy'].get('title', 'is null'),rep['policy'].get('description', '无').replace('<ul>','').replace('</ul>','').replace('<li>','').replace('</li>','').replace('<br>','').replace('</br>','').replace('&nbsp;','').replace(' ',''))
        if return_dict['changeInfo'].find('is null') != -1:
            return_dict['changeInfo'] = ''
        return_dict['agemin'] = agemin
        return_dict['agemax'] = agemax
        return_dict['ticket_3rd'] = ticket_3rd
        return_dict['info'] = info
        return_dict['date_price'] = get_date_price(rep, sku_id)
        sku_id += 1
        return_dict['ticketType'] = 1
        return_dict['price'] = price
        return_dict['id_3rd'] = str(rep['id'])
        return_ticket.append(return_dict)
    return return_ticket
    raise SkipException('无法生成票')


def load_json(resp):
    try:
        ret = json.loads(resp)
    except:
        traceback.print_exc()
        print resp
    return ret
