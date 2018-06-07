# -*- coding: utf-8 -*-
from mioji.common.mioji_struct import MFlight, MFlightLeg, MFlightSegment

from flighApibase import FlightApi
from tongchengBase import cabin, FOR_FLIGHT_DATE, changesTypes, changesStatuss, refundTypes, refundStatuss

import json


class tongchengFlightApi(FlightApi):

    source_type = 'tongchengApiFlight'
    targets = {'Flight': {'version': 'InsertNewFlight'}}
    old_spider_tag = {'tongchengApiFlight': {'required': ['Flight']}}

    def __init__(self, task=None):
        FlightApi.__init__(self, task=task)

    def parse_detail(self, req, resp):
        """

        :param req:
        :param resp:
        :return:
        """
        try:
            _i_ = 0
            all_ticket = []
            for step in resp['routings']:
                f = MFlight(MFlight.OD_ONE_WAY)
                f.price = step['adultPrice'] + step['adultTax']
                f.currency = 'CNY'
                f.source = 'tongchengApi'
                f.stopby = self.task.ticket_info['v_seat_type']
                rule = step['rule']
                mleg = MFlightLeg()
                for Segment in step['fromSegments']:
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
                    mleg.append_seg(ms)
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
                mleg.return_rule = mleg.change_rule = can_el
                baggages = rule['baggageInfoList']
                mleg.baggage = ''
                for item in baggages:
                    mleg.baggage = '第 %s 个行程, 大人: %s, 小孩: %s' % (item['segmentNo'], item['adultBaggage'], item['childBaggage'])

                mleg.change_rule = mleg.change_rule or 'NULL'
                mleg.return_rule = mleg.return_rule or 'NULL'
                mleg.baggage = mleg.baggage or 'NULL'
                mleg.others_info = json.dumps({
                    'payKey': {'redis_key': self.redis_key, 'id': _i_, 'data': step['data'],
                               'verify_num': self.task.ticket_info['v_count'], 'flight_info': step['fromSegments']},
                    'paykey': {'redis_key': self.redis_key, 'id': _i_, 'data': step['data'],
                               'verify_num': self.task.ticket_info['v_count'], 'flight_info': step['fromSegments']},
                    'rate_key': {},
                    'extra': {
                        'return_rule': '|'.join([mleg.change_rule, mleg.return_rule]),
                    },
                })

                _i_ += 1
                f.append_leg(mleg)
                all_ticket.append(f.convert_to_mioji_flight().to_tuple())
        except Exception as e:
            import traceback
            print traceback.format_exc(e)
        return all_ticket

if __name__ == '__main__':
    from mioji.common.task_info import Task

    task = Task()
    task.redis_key = 'flight|10001|20001|20180129|20180130|CA934'
    task.content = "PEK&ICN&20180322&20180323"
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