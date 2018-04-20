#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Created on 2017年03月31日

Updated on 2017-04-06

@author: hourong

@modify by dongkai

"""

from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import re
import time
import urllib
# from cleartrip_city_name_spider import ClearTripCityNameSpider
import cleartrip_city_name_spider
from datetime import datetime
from mioji.common.task_info import Task
from mioji.common.class_common import RoundFlight
from mioji.common.airline_common import Airline
from utils import seat_type_to_queryparam

real_class_map = dict(E='经济舱', B='商务舱', F='头等舱')


def compute_day_diff(stop_datetimes):
    day_diffs = []
    for i in xrange(0, len(stop_datetimes), 2):
        if stop_datetimes[i].day == stop_datetimes[i + 1].day:
            day_diffs.append('0')
        else:
            day_diffs.append('1')
    return '_'.join(day_diffs)


# 解析传进来的任务，获得任务参数


def content_parser(taskcontent, ticket_info):
    # 声明这个是全局变量，否则python会把它当成局部变量
    global total_passengers

    taskcontent_splited = taskcontent.split('&')
    dept_id, dest_id, dept_daystr, rdept_daystr = taskcontent_splited[0:4]
    year, month, day = [dept_daystr[0:4], dept_daystr[4:6], dept_daystr[6:]]
    dept_datetime = datetime(int(year), int(month), int(day))
    year, month, day = [rdept_daystr[0:4], rdept_daystr[4:6], rdept_daystr[6:]]
    rdept_datetime = datetime(int(year), int(month), int(day))

    # 创建任务词典，其中包含了所有需要的任务参数
    task_dict = dict(dept_id=dept_id, dest_id=dest_id,
                     dept_datetime=dept_datetime, rdept_datetime=rdept_datetime)

    # 从ticket_info获取舱位的信息，这里得到的是查询时使用的舱位，用的是英文

    task_dict['cabinclass'] = seat_type_to_queryparam(ticket_info.get('v_seat_type', 'E'))

    # 从ticket_info得到人数的信息，默认的乘客类型是成人
    task_dict['adults'] = ticket_info.get('v_count', 1)
    total_passengers = task_dict['adults']

    # 构造儿童和婴儿的人数
    task_dict['childs'] = 0
    task_dict['infants'] = 0

    return task_dict


def get_referer_url(task_dict):
    dept_id = task_dict['dept_id']
    dest_id = task_dict['dest_id']
    dept_datetime = task_dict['dept_datetime']
    rdept_datetime = task_dict["rdept_datetime"]
    adults = task_dict.get('adults', 1)
    childs = task_dict.get('childs', 0)
    infants = task_dict.get('infants', 0)
    cabinclass = task_dict.get('cabinclass', 'Economy')
    dept_daystr = dept_datetime.strftime('%d/%m/%Y')
    rdept_datetime = rdept_datetime.strftime('%d/%m/%Y')
    timestamp = format(time.time() * 1000, '.0f')
    url_referer_t = 'https://www.cleartrip.sa/flights/results/intlairjson?from={dept_id}&to={dest_id}&depart_date={dept_daystr}&return_date={rdept_datetime}&adults={adults}&childs={childs}&infants={infants}&class={cabinclass}&airline=&carrier=&intl=y&sd={timestamp}&page=loaded'.format(
      **locals())

    return url_referer_t


def get_json_url(task_dict):
    url_intlairjson0_t = 'https://www.cleartrip.sa/flights/results/intlairjson?trip_type=RoundTrip&origin={dept_city}&from={dept_id}&destination={dest_city}&to={dest_id}&depart_date={dept_daystr}&return_date={rdept_daystr}&adults={adults}&childs={childs}&infants={infants}&class={cabinclass}&airline=&carrier=&ver=V2&type=json&intl=y&sd={timestamp}&page=&search_ver=V2&cc=1&rhc=1'

    dept_id = task_dict['dept_id']
    dest_id = task_dict['dest_id']
    dept_datetime = task_dict['dept_datetime']
    rdept_datetime = task_dict["rdept_datetime"]
    adults = task_dict.get('adults', 1)
    childs = task_dict.get('childs', 0)
    infants = task_dict.get('infants', 0)
    cabinclass = task_dict.get('cabinclass', 'Economy')
    dept_daystr = dept_datetime.strftime('%d/%m/%Y')
    rdept_daystr = rdept_datetime.strftime("%d/%m/%Y")
    timestamp = format(time.time() * 1000, '.0f')

    task = Task('cleartrip::cleartrip', dept_id)
    spider = cleartrip_city_name_spider.ClearTripCityNameSpider()
    spider.task = task
    spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
    dept_city_unescaped = spider.result['City'][
        0].get('v', '')
    print "dept_city_unescaped:",dept_city_unescaped
    dept_city = urllib.quote_plus(dept_city_unescaped, safe='()')
    task = Task('cleartrip::cleartrip', dest_id)
    spider = cleartrip_city_name_spider.ClearTripCityNameSpider()
    spider.task = task
    spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
    dest_city_unescaped = spider.result['City'][
        0].get('v', '')
    dest_city = urllib.quote_plus(dest_city_unescaped, safe='()')
    dept_daystr = dept_datetime.strftime('%d%%2F%m%%2F%Y')
    rdept_daystr = rdept_datetime.strftime('%d%%2F%m%%2F%Y')
    url_intlairjson0 = url_intlairjson0_t.format(**locals())
    return url_intlairjson0, dest_city, dept_city

def change_time_type(params):

    print  '请求参数：',params.keys()
    dept_date = datetime.strptime(params['depart_date'],'%d/%m/%Y')
    params['depart_date'] = dept_date.strftime('%d%%2F%m%%2F%Y')
    rdept_date = datetime.strptime(params['return_date'],'%d/%m/%Y')
    params['return_date'] = rdept_date.strftime('%d%%2F%m%%2F%Y')
    return params

def get_city_name(mj_city_id):
    spider = cleartrip_city_name_spider.ClearTripCityNameSpider()
    spider.task = Task('cleartrip::cleartrip', mj_city_id)
    spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
    city_info = spider.result['City'][0].get('v', '')
    return city_info


def roundtrip_base_params(task_dict):
    """
    """
    ret = {
        "trip_type": "RoundTrip",
        "type": "json",
        "ver": "V2",
        "cc": 1,
        "timeout": 3000,
        "airline": '',
        "carrier": '',
        'search_ver': 'V2',
        'page': 'loaded'
    }
    ret["from"] = task_dict['dept_id']
    ret["origin"] = get_city_name(task_dict['dept_id'])
    ret["destination"] = get_city_name(task_dict["dest_id"])
    ret["to"] = task_dict["dest_id"]
    ret["depart_date"] = task_dict["dept_datetime"].strftime('%d/%m/%Y')
    ret["return_date"] = task_dict["rdept_datetime"].strftime('%d/%m/%Y')
    ret["sd"] = format(time.time() * 1000, '.0f')
    ret["adults"] = task_dict.get('adults', 1)
    ret["childs"] = task_dict.get('childs', 0)
    ret["infants"] = task_dict.get('infants', 0)
    ret["class"] = task_dict.get('cabinclass', 'Economy')
    ret["intl"] = "y"
    return ret


# 处理contents，contents中是所有的单程机票信息
def process_contents(contents_raw):
    contents = {}
    for content_i, content_r in contents_raw.iteritems():
        content = contents[content_i] = {}
        content['dur'] = content_r['dr']
        content['from'] = content_r['fr']
        content['to'] = content_r['to']

        s_datestr = re.search('\d{8}_\d{2}:\d{2}', content_r['fk']).group()
        content['s_datetime'] = datetime.strptime(
            s_datestr, '%d%m%Y_%H:%M').strftime('%Y-%m-%dT%H:%M:%S')  # 出发时间

        e_datestr = content_r['ad'] + content_r['a']
        content['e_datetime'] = datetime.strptime(
            e_datestr, '%d/%m/%Y%H:%M').strftime('%Y-%m-%dT%H:%M:%S')  # 到达时间

        content['flight_no'] = re.search(
            '[A-Z1-9]+-\d+', content_r['fk']).group()
        content['airline'] = Airline.get(re.search('[A-Z0-9]+', content['flight_no']).group(
        ), re.search('[A-Z0-9]+', content['flight_no']).group())  # 航空公司
        content['flight_no'] = content['flight_no'].replace('-', '')
        content['seat_type'] = content_r['fk'][-1]  # 座位类型
    return contents


def page_parser(page_dict, task_dict):
    allflights = []
    # 处理contents的内容格式，其中包含了每一个单程机票的信息
    contents_raw = page_dict['content']
    # import pdb;pdb.set_trace()
    contents = process_contents(contents_raw)

    # 这是所有的价格信息
    fare = page_dict['fare']

    # 这是货币单位
    currency = page_dict['jsons']['searchType']['disp_currency']

    # page_dict['mapping']['onward']中是所有往返的组合，遍历则可得到所有的往返机票信息
    for mapping in page_dict['mapping']['onward']:
        roundflight = RoundFlight()

        flight_nos = []
        plane_nos = []
        airlines = []
        durs = []
        seat_types = []
        real_classes = []
        stop_ids = []
        stop_times = []

        # 这是去程，中间可能有转机
        for flight_a in mapping['c'][0]:
            # 得到航班号
            flight_nos.append(contents[flight_a]['flight_no'])

            # 得到航空公司
            airlines.append(contents[flight_a]['airline'])

            # 得到机型
            plane_nos.append('NULL')

            # 得到飞行时间
            durs.append(contents[flight_a]['dur'])

            # 得到座位类型
            seat_types.append(real_class_map[contents[flight_a]['seat_type']])

            # 得到真实座位类型
            real_classes.append('NULL')

            # 得到stop_id
            stop_ids.append(contents[flight_a]['from'])
            stop_ids.append(contents[flight_a]['to'])

            # 得到stop_time
            stop_times.append(contents[flight_a]['s_datetime'])
            stop_times.append(contents[flight_a]['e_datetime'])

        roundflight.flight_no_A = '_'.join(flight_nos)
        roundflight.airline_A = '_'.join(airlines)
        roundflight.plane_no_A = '_'.join(plane_nos)
        roundflight.dept_time_A = stop_times[0]
        roundflight.dest_time_A = stop_times[-1]
        roundflight.dur_A = sum(map(int, durs))
        roundflight.seat_type_A = '_'.join(seat_types)
        roundflight.real_class_A = '_'.join(real_classes)
        roundflight.stop_id_A = '|'.join('%s_%s' % tuple(
            stop_ids[i:i + 2]) for i in xrange(0, len(stop_ids), 2))
        roundflight.stop_time_A = '|'.join('%s_%s' % tuple(
            stop_times[i:i + 2]) for i in xrange(0, len(stop_times), 2))
        roundflight.daydiff_A = compute_daydiff(stop_times)
        roundflight.stop_A = len(flight_nos) - 1

        flight_nos = []
        plane_nos = []
        airlines = []
        durs = []
        seat_types = []
        real_classes = []
        stop_ids = []
        stop_times = []

        # 这是返程，中间也可能有转机
        for flight_b in mapping['c'][1]:
            # 得到航班号
            flight_nos.append(contents[flight_b]['flight_no'])

            # 得到航空公司
            airlines.append(contents[flight_b]['airline'])

            # 得到机型
            plane_nos.append('NULL')

            # 得到飞行时间
            durs.append(contents[flight_b]['dur'])

            # 得到座位类型
            seat_types.append(real_class_map[contents[flight_b]['seat_type']])

            # 得到真实座位类型
            real_classes.append('NULL')

            # 得到stop_id
            stop_ids.append(contents[flight_b]['from'])
            stop_ids.append(contents[flight_b]['to'])

            # 得到stop_time
            stop_times.append(contents[flight_b]['s_datetime'])
            stop_times.append(contents[flight_b]['e_datetime'])

        roundflight.flight_no_B = '_'.join(flight_nos)
        roundflight.airline_B = '_'.join(airlines)
        roundflight.plane_no_B = '_'.join(plane_nos)
        roundflight.dept_time_B = stop_times[0]
        roundflight.dest_time_B = stop_times[-1]
        roundflight.dur_B = sum(map(int, durs))
        roundflight.seat_type_B = '_'.join(seat_types)
        roundflight.real_class_B = '_'.join(real_classes)
        roundflight.stop_id_B = '|'.join('%s_%s' % tuple(
            stop_ids[i:i + 2]) for i in xrange(0, len(stop_ids), 2))
        roundflight.stop_time_B = '|'.join('%s_%s' % tuple(
            stop_times[i:i + 2]) for i in xrange(0, len(stop_times), 2))
        roundflight.daydiff_B = compute_daydiff(stop_times)
        roundflight.stop_B = len(flight_nos) - 1

        # 处理去程和返程共同的信息
        roundflight.dept_id = roundflight.stop_id_A[0:3]
        roundflight.dest_id = roundflight.stop_id_A[-3:]
        roundflight.dept_day = roundflight.dept_time_A[0:10]
        roundflight.dest_day = str(task_dict['rdept_datetime'])[0:10]
        roundflight.currency = currency
        roundflight.source = 'cleartrip::cleartrip'

        # 处理价格，退改签，优惠等信息，这里入库的价格是平均价格，即总价格除以总人数
        ticket_i = mapping['f']  # 这是这种选择的价格的编号
        global total_passengers  # 需要用这个全局变量来算平均价格，和平均的税
        roundflight.price = fare[ticket_i][fare[ticket_i]
        ['dfd']]['bp'] / total_passengers # base fare
        roundflight.tax = fare[ticket_i][fare[ticket_i]
        ['dfd']]['t'] / total_passengers

        allflights.append((roundflight.dept_id, roundflight.dest_id, roundflight.dept_day, roundflight.dest_day,
                           roundflight.price, roundflight.tax, roundflight.surcharge, roundflight.promotion,
                           roundflight.currency, roundflight.source, roundflight.return_rule, roundflight.flight_no_A,
                           roundflight.airline_A, roundflight.plane_no_A, roundflight.dept_time_A,
                           roundflight.dest_time_A, roundflight.dur_A, roundflight.seat_type_A,
                           roundflight.real_class_A, roundflight.stop_id_A, roundflight.stop_time_A,
                           roundflight.daydiff_A, roundflight.stop_A, roundflight.flight_no_B,
                           roundflight.airline_B, roundflight.plane_no_B, roundflight.dept_time_B,
                           roundflight.dest_time_B, roundflight.dur_B, roundflight.seat_type_B,
                           roundflight.real_class_B, roundflight.stop_id_B, roundflight.stop_time_B,
                           roundflight.daydiff_B, roundflight.stop_B, roundflight.change_rule,
                           roundflight.share_flight_A, roundflight.share_flight_B, roundflight.stopby_A,
                           roundflight.stopby_B, roundflight.baggage, roundflight.transit_visa,
                           roundflight.reimbursement, roundflight.flight_meals, roundflight.ticket_type,
                           roundflight.others_info, '-1'))  # 最后这个是余票

    return allflights


def compute_daydiff(stop_datetimes):
    daydiffs = []
    for i in xrange(0, len(stop_datetimes), 2):
        if stop_datetimes[i][8:10] == stop_datetimes[i + 1][8:10]:
            daydiffs.append('0')
        else:
            daydiffs.append('1')
    return '_'.join(daydiffs)
