# -*- coding: utf-8 -*-
from mioji.common.mioji_struct import MFlight, MFlightLeg, MFlightSegment

from flighApibase import FlightApi
from tongchengBase import cabin, FOR_FLIGHT_DATE, changesTypes, changesStatuss, refundTypes, refundStatuss

import json


class tongchengFlightApi(FlightApi):

    source_type = 'tongchengApiRoundFlight'
    targets = {'Flight': {'version': 'InsertRoundFlight2'}}
    old_spider_tag = {'tongchengApiRoundFlight': {'required': ['Flight']}}

    def __init__(self, task=None):
        FlightApi.__init__(self, task=task)

    def parse_detail(self, req, resp):
        """

        :param req:
        :param resp:
        :return:
        """
        all_ticket = []
        _i_ = 0
        count_i = 0
        for step in resp['routings']:
            f = MFlight(MFlight.OD_ROUND)
            f.price = step['adultPrice'] + step['adultTax']
            f.tax = step['adultTax']
            f.currency = 'CNY'
            f.source = 'tongchengApi'
            f.stopby = self.task.ticket_info['v_seat_type']

            rule = step['rule']
            for legObj, Segments in zip([MFlightLeg(), MFlightLeg()], [step['fromSegments'], step['retSegments']]):
                for Segment in Segments:
                    ms = MFlightSegment()
                    ms.flight_no = Segment['flightNumber']
                    ms.plane_type = Segment['aircraftCode']
                    ms.flight_corp = Segment['carrier']
                    ms.seat_type = cabin[Segment['cabinGrade']]
                    ms.real_class = Segment['cabinGrade']
                    ms.dept_id = Segment['depAirport']
                    ms.dest_id = Segment['arrAirport']
                    ms.set_dept_date(Segment['depTime'], FOR_FLIGHT_DATE)
                    ms.set_dest_date(Segment['arrTime'], FOR_FLIGHT_DATE)
                    if Segment['codeShare']:
                        ms.share_flight = Segment['operatingFlightNumber']

                    legObj.append_seg(ms)
                changes = rule['changesInfoList']
                refunds = rule['refundInfoList']
                can_el = '重要提示：实际退改费用以退改说明为准<br />'
                for i in range(len(changes)):
                    if changes[i]['changesStatus'] in ['E', 'H'] and refunds[i]['refundStatus'] in ['E', 'H']:
                        can_el += '退票说明：' + refunds[0]['cnRemark'] + '<br />退票费用：' + refunds[0]['refundFee'] + \
                                  refunds[0].get('currency', 'CNY') + '<br />改期说明：' + changes[0]['cnRemark'] + \
                                  '<br />改期费用：' + changes[0]['changesFee'] + changes[0].get('currency', 'CNY')
                    elif changes[i] == 'T' and refunds[i] == 'T':
                        can_el += '退票说明：订单不可取消<br />改期说明：订单不可改期'
                    elif changes[i] == 'F' and refunds[i] == 'F':
                        can_el += '退票说明：订单可免费取消<br />改期说明：订单可免费改期'
                    else:
                        pass
                legObj.return_rule = legObj.change_rule = can_el
                baggages = rule['baggageInfoList']
                legObj.baggage = ''
                for item in baggages:
                    if item.get('adultBaggage', None):
                        legObj.baggage += '第 %s 个行程, 大人行李: %s, 小孩行李: %s' % (item.get('segmentNo',''), item.get('adultBaggage',''), item.get('childBaggage',''))
                legObj.change_rule = legObj.change_rule or 'NULL'
                legObj.return_rule = legObj.return_rule or 'NULL'
                legObj.baggage = legObj.baggage or 'NULL'
                if count_i % 2 == 0:
                    legObj.others_info = json.dumps({
                        'payKey': {'redis_key': self.redis_key, 'id': _i_, 'data': step['data'],
                                   'verify_num': self.task.ticket_info['v_count'],
                                   'flight_info': step['fromSegments'], 'flight_ret_info': step['retSegments']},
                        'paykey': {'redis_key': self.redis_key, 'id': _i_, 'data': step['data'],
                                   'verify_num': self.task.ticket_info['v_count'],
                                   'flight_info': step['fromSegments'], 'flight_ret_info': step['retSegments']},
                        'rate_key': {},
                        'extra': {
                            'return_rule': '|'.join([legObj.change_rule, legObj.return_rule]),
                        },
                    })
                else:
                    legObj.others_info = 'NULL'
                f.append_leg(legObj)
                count_i += 1
            _i_ += 1

            all_ticket.append(f.convert_to_mioji_flight().to_tuple())
        final_tickets = []
        for i in all_ticket:
            i = list(i)
            i[10] = i[10].split('&')[0]
            i[35] = i[10]
            final_tickets.append(tuple(i))
        return final_tickets

if __name__ == '__main__':
    from mioji.common.task_info import Task

    task = Task()
    task.redis_key = 'flightround|10001|20001|20180129|20180130|CA934'
    task.content = "SHA&HKG&20180524&20180527"
    task.other_info = {}
    task.ticket_info = {"v_count": 1,
                        'v_seat_type': 'E',
                        "auth": json.dumps({
                            # "url": "http://tcflightopenapi.t.17usoft.com/flightdistributeapi/dispatcher/api",#测试补鞥用
                            "url": "http://tcflightopenapi.17usoft.com/flightdistributeapi/dispatcher/api",  # 正式能用
                            "safe_code": "5fe87fe834c2e726",
                            "pid": "6a054f5fda424be5947ff1124c1f66af",
                            "session_key": "6101b16a2bb5ea1b3844ed78120ffe8b919e840dbd0f9c72074082786"
                        })}
    spider = tongchengFlightApi(task)

    spider.task = task
    result_code = spider.crawl()
    print result_code
    print json.dumps(spider.result['Flight'], ensure_ascii=False)