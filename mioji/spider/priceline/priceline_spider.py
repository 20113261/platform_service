#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import json
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.class_common import Flight

header = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
    "Content-Type": "application/json;charset=UTF-8",
}

# dicts
seat_dict = {'ECO': '经济舱', 'BUS': '商务舱', 'FST': '头等舱', 'PEC': '超级经济舱'}
class_code_dict = {'E': 'ECO', 'B': 'BUS', 'F': 'FST', 'P': 'PEC'}
class_dict = {'5': '超级经济舱', '1': '头等舱', '2': '商务舱', '3': '经济舱'}
# re
pat = re.compile(r'<meta name="jwt" content="(.*?)">')
pat_day = re.compile('\d\d\d\d-\d\d-\d\d')
pat_time = re.compile('\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d')

# urls
home_url = 'https://www.priceline.com/'
carl_url_base = 'https://www.priceline.com/m/fly/search/'
list_url = "https://www.priceline.com/m/fly/search/api/listings"

# No ticket warning
no_ticket_warning = 'No flights are available for your selected itinerary. Please select new airports or dates and try searching again'


class PricelineFlightSpider(Spider):
    source_type = 'priceline'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'Flight': {'version': 'InsertNewFlight'}
    }

    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'pricelineFlight': {'required': ['Flight']}
    }

    def __init__(self, task=None):
        Spider.__init__(self, task=task)
        # 任务信息
        self.adults = 1
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
            "Content-Type": "application/json;charset=UTF-8",
        }
        self.dept_id = None
        self.dest_id = None
        self.dept_day = None
        self.dept_day_formatted = None
        self.seat = None
        # 链接
        self.crawl_url = carl_url_base
        self.sess_url = carl_url_base

        # 处理这些信息
        if task:
            self.process_task_info()
            self.crawl_url = self.get_carl_url()

        # 爬取的某些参数
        self.head_id = 1
        self.end_id = 40
        self.offset = 40

        self.tickets = []

    def targets_request(self):
        if self.dept_day_formatted is None:
            self.process_task_info()
            self.crawl_url = self.get_carl_url()

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def first_page():
            '''
            data 如需要保存结果，指定data.key
            这个请求只需要访问主页
            '''
            return {
                'req': {'url': home_url, 'headers': self.header}
            }

        @request(retry_count=1, proxy_type=PROXY_FLLOW)
        def second_page():
            '''
            data 如需要保存结果，指定data.key
            这个请求访问 /m/fly/search 获取token
            '''
            return {
                'req': {'url': self.crawl_url, 'headers': self.header},
                'user_handler': [self.get_token]
                # 'data': {'content_type': 'html'},
            }

        @request(retry_count=2, proxy_type=PROXY_FLLOW, binding=['Flight'])
        def list_pages():
            offset = 40
            self.head_id = 1
            self.end_id = offset

            pages = []
            for p in range(3):
                postdata = self.get_postdata()
                self.end_id += offset
                self.head_id = self.end_id - offset + 1

                pages.append({
                    'req': {'method': "POST", 'url': list_url, 'data': postdata, 'headers': self.header},
                    'data': {'content_type': 'json'},
                    'user_handler': [self.assert_response]
                })
            return pages

        return [first_page, second_page, list_pages]

    def respon_callback(self, req, resp):
        pass

    def check_list_result(self, list_result):
        # all 0 -> 0
        # all 29 -> 29
        # has 0 and other error:
        #  all 23, 23, 24 -> network error
        #  29 and network error -> 29
        result, all_except, all_ok, one_exception = list_result
        if result:
            return result, 0
        else:
            return result, 29

    def assert_response(self, req, json_data):
        if json_data["resultCode"] != 0:
            raise parser_except.ParserException(parser_except.DATA_NONE,
                                                '返回的resultCode不为0')
        if json_data["resultMessage"] != 'Success':
            raise parser_except.ParserException(parser_except.DATA_NONE,
                                                '返回的resultMessage不为Success')

    def parse_Flight(self, req, json_data):
        tickets = []
        # 这个不需要判断了吧
        currency = json_data['airSearchRsp']['pointOfSale']['currency']

        slice_dict = {}
        if 'slice' not in json_data['airSearchRsp']:
            return tickets
        for x in json_data['airSearchRsp']["slice"]:
            slice_dict[x["uniqueSliceId"]] = x
        seg_dict = {}
        for x in json_data['airSearchRsp']['segment']:
            seg_dict[x['uniqueSegId']] = x

        itineraries = json_data['airSearchRsp']['pricedItinerary']
        for itinerary in itineraries:
            flight = Flight()  # 每张机票对应一个航班

            # 只是简单地算下价格..
            server_fee = itinerary["pricingInfo"]["fees"][0]["amount"]
            # tax = itinerary["pricingInfo"]["totalTaxes"]
            totalFare = itinerary["pricingInfo"]["totalFare"]
            flight.price = server_fee + totalFare
            flight.rest = itinerary.get('numSeats', 0)

            uniqueSlice = slice_dict[itinerary['slice'][0]['uniqueSliceId']]
            flight.dur = int(uniqueSlice['duration']) * 60

            stop_id = []
            stop_time = []
            plane_no = []
            flight_no = []
            seat_type = []
            plane_type = []
            for seg in uniqueSlice['segment']:
                segment = seg_dict[seg['uniqueSegId']]
                stop_id.append(segment['origAirport'] + '_' + segment['destAirport'])
                stop_time.append(segment['departDateTime'] + '_' + segment['arrivalDateTime'])
                plane_no.append(segment['equipmentCode'])
                flight_no.append(segment['marketingAirline'] + segment['flightNumber'])
                seat_type.append(seat_dict[seg['cabinClass']])
                plane_type.append('NULL')  # 暂时对应不起来

            flight.dept_id = stop_id[0].split('_')[0]
            flight.dest_id = stop_id[-1].split('_')[-1]
            flight.dept_day = self.dept_day_formatted
            flight.tax = 0
            flight.currency = currency
            flight.source = 'priceline::priceline'
            # flight_stop = len(stop_id) - s1
            flight.plane_no = '_'.join(plane_no)
            flight.plane_type = '_'.join(plane_type)
            flight.flight_no = '_'.join(flight_no)
            flight.dept_time = stop_time[0].split('_')[0]
            flight.dest_time = stop_time[-1].split('_')[-1]
            flight.real_class = flight.seat_type = '_'.join(seat_type)
            flight.stop_id = '|'.join(stop_id)
            flight.stop_time = '|'.join(stop_time)
            flight.daydiff = flight.get_day_diff()
            flight.airline = flight.get_airline()

            tickets.append(flight.to_tuple())
        self.tickets.extend(tickets)
        return tickets

    def process_task_info(self):
        ticket_info = self.task.ticket_info
        seat_type = ticket_info.get('v_seat_type', 'E')
        self.adults = int(ticket_info.get('v_count', '2'))

        try:
            self.dept_id, self.dest_id, self.dept_day = self.task.content.split('&')
        except:
            raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                'Content Error:{0}'.format(self.task.content))
        # self.dept_day_formatted = dt.strptime(dept_day, '%Y%m%d').strftime('%Y-%m-%d')
        self.dept_day_formatted = self.dept_day[:4] + '-' + self.dept_day[4:6] + '-' + self.dept_day[6:]
        self.seat = class_code_dict[seat_type]

    def get_carl_url(self, carbin_class='ECO', child_num=0):
        if child_num:
            return carl_url_base + self.dept_id + '-' + self.dest_id + '-' + \
                   self.dept_day + '/?cabin-class=' + self.seat + '&num-adults=' + \
                   str(self.adults) + '&num-children=' + str(child_num)
        self.carl_url = carl_url_base + self.dept_id + '-' + self.dest_id + '-' + self.dept_day + '/?cabin-class=' + self.seat + '&num-adults=' + str(
            self.adults)
        return carl_url_base + self.dept_id + '-' + self.dest_id + '-' + self.dept_day + '/?cabin-class=' + self.seat + '&num-adults=' + str(
            self.adults)

    def get_token(self, req, data):
        if no_ticket_warning in data:
            raise parser_except.ParserException(99, "priceline::不支持航线/日期")
        try:
            token = pat.findall(data)[0]
        except:
            raise parser_except.ParserException(parser_except.PROXY_INVALID, "cannot find token")
        self.header['Referer'] = self.carl_url
        self.header['token-payload'] = token
        self.header['Connection'] = 'keep-alive'
        self.header['Content-Type'] = 'application/json;charset=UTF-8'

    def get_sess_url(self):
        self.sess_url = carl_url_base + self.dept_id + '-' + self.dest_id + '-' + self.dept_day

    def get_postdata(self):
        postdata = {
            "airSearchReq": {
                "requestId": "028477a55194eea7bdee74e21293c4c3",
                "clientSessionId": "d3895d041553b49aa96e4f2dedfbd6a7",
                "trip": {
                    "disclosure": "DISCLOSED",
                    "slice": [
                        {
                            "id": 1,
                            "departDate": self.dept_day_formatted,
                            "origins": {
                                "location": self.dept_id,
                                "type": "AIRPORT"
                            },
                            "destinations": {
                                "location": self.dest_id,
                                "type": "AIRPORT"
                            }
                        }
                    ]
                },
                "expressDeal": {
                    "slice": [
                        {
                            "id": 1,
                            "departDate": self.dept_day_formatted,
                            "origins": {
                                "location": self.dept_id,
                                "type": "AIRPORT"
                            },
                            "destinations": {
                                "location": self.dest_id,
                                "type": "AIRPORT"
                            }
                        }
                    ],
                    "openJawAllowed": True,
                    "allowedAlternates": [
                        "AIRPORT"
                    ]
                },
                "passenger": [
                    {
                        "type": "ADT",
                        "numOfPax": self.adults
                    }
                ],
                "searchOptions": {
                    "jetOnly": False,
                    "numOfStops": 7,
                    "cabinClass": self.seat,
                    "includeFusedItineraries": True
                },
                "liveSearchForAlternateDates": False,
                "liveSearchExpDealsForAlternateDates": False,
                "displayParameters": {
                    "sliceRefId": [
                        1
                    ],
                    "lowerBound": str(self.head_id),
                    "upperBound": str(self.end_id)
                },
                "filter": {
                    "alternates": {
                        "excludeDates": True,
                        "excludeAirports": True
                    }
                },
                "sortPrefs": [
                    {
                        "priority": 1,
                        "type": "PRICE",
                        "sliceRefId": 1,
                        "order": "ASC"
                    },
                    {
                        "priority": 1,
                        "type": "DEPARTTIME",
                        "sliceRefId": 1,
                        "order": "ASC"
                    }
                ],
                "includeAlternateSummary": False,
                "includeFullTripSummary": True,
                "includeFilteredTripSummary": True,
                "includeSliceSummary": True,
                "advDuplicateTimesItinFilter": False,
                "advSameDepartureItinFilter": False,
                "advSimDepartSimDurationItinFilter": False,
                "referrals": [
                    {
                        "external": {
                            "refClickId": "",
                            "refId": "DIRECT",
                            "referralSourceId": "DT"
                        }
                    }
                ]
            }
        }
        postdata = get_postdata(self.dept_id, self.dest_id, self.dept_day_formatted, self.seat, self.adults, 0,
                                str(self.head_id), str(self.end_id))
        return postdata


def get_postdata(dept, dest, date, seat='ECO', adult_num=1, child_num=0, head='1', end='40'):
    adults = adult_num + child_num
    postdata = '{"airSearchReq":{"requestId":"b25d03680cfd4b9cbf98134f84215168","clientSessionId":"badec60d6dcf6560f778ea86540bb676","trip":{"disclosure":"DISCLOSED","slice":[{"id":1,"departDate":"' + date + '","origins":{"location":"' + dept + '","type":"AIRPORT"},"destinations":{"location":"' + dest + '","type":"AIRPORT"}}]},"expressDeal":{"slice":[{"id":1,"departDate":"' + date + '","origins":{"location":"' + dept + '","type":"AIRPORT"},"destinations":{"location":"' + dest + '","type":"AIRPORT"}}],"openJawAllowed":true,"allowedAlternates":["AIRPORT"]},"passenger":[{"type":"ADT","numOfPax":' + str(
        adults) + '}],"searchOptions":{"jetOnly":false,"numOfStops":7,"cabinClass":"' + seat + '","includeFusedItineraries":true},"liveSearchForAlternateDates":false,"liveSearchExpDealsForAlternateDates":false,"displayParameters":{"sliceRefId":[1],"lowerBound":' + head + ',"upperBound":' + end + '},"filter":{"alternates":{"excludeDates":true,"excludeAirports":true}},"sortPrefs":[{"priority":1,"type":"PRICE","sliceRefId":1,"order":"ASC"},{"priority":1,"type":"DEPARTTIME","sliceRefId":1,"order":"ASC"}],"includeAlternateSummary":false,"includeFullTripSummary":true,"includeFilteredTripSummary":true,"includeSliceSummary":true,"advDuplicateTimesItinFilter":false,"advSameDepartureItinFilter":false,"advSimDepartSimDurationItinFilter":false,"referrals":[{"external":{"refClickId":"","refId":"DIRECT","referralSourceId":"DT"}}]}}'
    return postdata


def save_resp_file(content, called_count=[0], endwith='json'):
    file_name = "tmp%s.%s" % (called_count[0], endwith)
    with open(file_name, 'w') as fd:
        fd.write(content)
    called_count[0] += 1


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_http_proxy, simple_get_socks_proxy

    mioji.common.spider.get_proxy = simple_get_http_proxy
    task = Task()
    task.ticket_info = {}
    # task.content = 'PEK&ORD&20170919'
    task.content = 'KIX&XIY&20170910'
    spider = PricelineFlightSpider()
    spider.task = task
    print(spider.source_type)
    print(spider.crawl())
    print(spider.result)
    # print len(spider.tickets)
    # for item in spider.tickets:
    #     print item
