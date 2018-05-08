#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import time
import json
from lxml import etree
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import tostring
from mioji.common.task_info import Task
from mioji.common import parser_except
from mioji.common.class_common import Train
from mioji.common.spider import Spider, request, PROXY_NEVER


class Re4aRailSpider(Spider):
    source_type = 'raileuropeApiRail'
    targets = {
        'trains': {'version': 'InsertNewTrain'}}
    old_spider_tag = {
        'raileuropeApiRail': {'required': ['trains']}
    }

    def __init__(self, task=None):
        super(Re4aRailSpider, self).__init__(task=task)
        self._len = 1
        self.dept_time = ""
        self.start_time = ""
        self.trainnumber = "0"
        self.solutionid_num = 0
        self.trainrequest = "false"
        self._from = ""
        self._to = ""

    def make_content(self):
        self.task.ticket_info['auth'] = '{"key":"8780929146871554943","url":"https://webservicesx.euronet.vsct.fr/V10/webservices/xml"}'
        origin_city_code, destination_city_code, departure_data = self.content_parser()
        try:
            auth = json.loads(self.task.ticket_info['auth'])
            key = auth['key']
        except Exception:
            raise parser_except.ParserException(121, "key可能为空")
        adults = self.task.ticket_info.get('v_count', 2)
        if not self.task.ticket_info.get('dept_time'):
            dept_time = self.task.ticket_info.get('dept_time', '00:30')[-5:].replace(' ', '')
            dptime = (datetime.strptime(dept_time, '%H:%M') + timedelta(minutes=-29)).strftime("%H:%M")
            dstime = (datetime.strptime(dept_time, '%H:%M') + timedelta(minutes=1409)).strftime("%H:%M")
        else:
            dept_time = self.task.ticket_info.get('dept_time', '09:00')[-5:].replace(' ', '')
            dptime = (datetime.strptime(dept_time, '%H:%M') + timedelta(minutes=-30)).strftime("%H:%M")
            dstime = (datetime.strptime(dept_time, '%H:%M') + timedelta(minutes=30)).strftime("%H:%M")
        return {
            "key": key,
            "originCityCode": origin_city_code,
            "destinationCityCode": destination_city_code,
            "departureDate": departure_data,
            "departureTime": "<low>{}</low><high>{}</high>".format(dptime, dstime),
            "nAdults": adults,
            "nChildren": 0,
            "childrenAge": "<int>0</int>",
            "nYouth": 0,
            "youthAge": 0,
            "nSeniors": 0,
            "nPassHolders": 0,
            "packageType": "PRICE_DRIVEN",
            "fareTypes": "RETAIL",
            "roundtripMode": "FORWARD_ONLY",
            "groupMode": "INDIVIDUAL",
            "storeOTSegmentSchedule": "false",
            "useFullDayResult": "false",
            "laterTrainInfo": "<isLaterTrainRequest>{}</isLaterTrainRequest>"
                              "<latestTrainNumber>{}</latestTrainNumber>"
                              "<latestTrainDepartureTime>{}</latestTrainDepartureTime>".format(self.trainrequest,
                                                                                               self.trainnumber,
                                                                                               self.dept_time)}

    @staticmethod
    def dict_to_xml(tag, content):
        elements = Element(tag)
        for k, v in content.items():
            child = Element(k)
            child.text = str(v)
            elements.append(child)
        return elements

    def targets_request(self):
        self.start_time = time.time()
        self.task.ticket_info['auth'] = '{"key":"8780929146871554943","url":"https://webservicesx.euronet.vsct.fr/V10/webservices/xml"}'
        auth = json.loads(self.task.ticket_info['auth'])
        try:
            url = auth['url']
        except Exception:
            raise parser_except.ParserException(121, "url可能为空")

        @request(retry_count=3, proxy_type=PROXY_NEVER, binding=self.parse_trains)
        def pages_request():
            raw_data = tostring(self.dict_to_xml('request', self.make_content()))
            data = re.sub("<request><", '<request serviceName="BuildPackageForCityPair"><', raw_data).replace(
                "&lt;", "<").replace("&gt;", ">")
            return {'req': {
                'method': 'POST',
                'url': url,
                'data': data,
            }}

        yield pages_request

        while int(self.solutionid_num) >= 5:
            if (time.time() - self.start_time) > 60:
                break
            yield pages_request

    def content_parser(self):
        content_list = self.task.content.split('&')
        self._from = content_list[0]
        origin_city_code = content_list[1]
        self._to = content_list[2]
        destination_city_code = content_list[3]
        check_data = datetime.strptime(content_list[4], "%Y%m%d")
        departure_data = check_data.strftime("%Y-%m-%d")
        return origin_city_code, destination_city_code, departure_data

    def get_solution(self, root):
        return root.xpath("//solution")

    def get_segment(self, solution):
        _seg = []
        segments = solution.xpath('.//segments')
        for segment in segments:
            _seg.append(segment.xpath('segment'))
        return segments

    def len_seg(self, segments):
        self._len = len(segments)
        return len(segments)

    def seg_join(self, segments):
        _seg = list()
        for seg in segments:
            ori = seg.xpath('originStationCode/text()')[0]
            des = seg.xpath('destinationStationCode/text()')[0]
            _seg.append("".join(['%s_%s' % (ori, des)]))
        return "|".join(_seg)

    def time_join(self, segments):
        _time = list()
        for seg in segments:
            dep = seg.xpath('departureDateTime/text()')[0] + ":00"
            arr = seg.xpath('arrivalDateTime/text()')[0] + ":00"
            _time.append("".join(['%s_%s' % (dep, arr)]))
        return "|".join(_time)

    def tra_join(self, trains):
        _tra = list()
        for train in trains:
            equipment_code = train.xpath('train/equipmentCode/text()')[0]
            train_number = train.xpath('train/trainNumber/text()')[0]
            _tra.append("".join([equipment_code+train_number]))
        return "_".join(_tra)

    def equip_list(self, trains):
        _equ = list()
        for train in trains:
            equipment_code = train.xpath('train/equipmentCode/text()')[0]
            _equ.append(equipment_code)
        return _equ

    def equip_json(self, trains, equipments):
        names = list()
        for equ in equipments:
            equs = equ.split('_')
            if equs[0] != '':
                for e, n in zip(equs, self.equip_list(trains)):
                    if e == "FRENCH JOURNEY":
                        names.append(e+' '+n)
                    else:
                        names.append(e)
        return names

    def city_code(self, citys):
        _city = list()
        for city in citys:
            ori = city.xpath('originCityName/text()')[0]
            des = city.xpath('destinationCityName/text()')[0]
            _city.append("_".join([ori, des]))
        return "_".join(_city)

    def rules_join(self, rules):
        _rule = list()
        for rule in rules:
            _rule.append("|".join(rule))
        return _rule

    def corp_join(self, corp):
        _corp = list()
        for cor in corp:
            _corp.append("_".join(cor))
        return _corp

    def class_join(self, corp):
        _corp = list()
        for cor in corp:
            _corp.append("|".join(cor))
        return _corp

    def diff_join(self, times):
        _diff = list()
        for time in times.split('|'):
            if time[8:10] == time[-11:-9]:
                _diff.append('0')
            else:
                _diff.append("1")
        return "_".join(_diff)

    def real_join(self, times):
        _diff = list()
        for time in times.split('|'):
            if time == "TICKET_PLUS_RESERVATION":
                _diff.append('1')
            else:
                _diff.append("0")
        return "_".join(_diff)

    def split_rules(self, rules):
        return [rules[i:i+self._len] for i in range(0, len(rules), self._len)]

    def split_city(self, city):
        return [city[i:i + 2] for i in range(0, len(city), 2)]

    def get_package(self, trains, solution):
        ticket = list()
        all_ticket = list()
        train_dict = {'first': '一等舱', 'second': '二等舱'}
        package_pre = "packagePrices/{}ClassPrices/accommodationPrice/packages/package"
        for i in ['first', 'second']:
            prices = solution.xpath("{}/price/amount/text()".format(package_pre.format(i)))
            package_fare_id = solution.xpath('{}/packageFareId/text()'.format(package_pre.format(i)))
            passage_type = solution.xpath('{}/reservationStatus/text()'.format(
                package_pre.format(i)))
            printing_options_applicable = solution.xpath('{}/printingOptionsApplicable'.format(package_pre.format(i)))
            _fun = lambda x: re.sub('_|  ', ' ', x)
            f_names = _fun(
                ",".join(solution.xpath('{}/fareDetails/productFare/familyName/text()'.format(
                    package_pre.format(i))))).split(',')
            s_rules = solution.xpath('{}/fareDetails/productFare/saleRules/text()'.format(package_pre.format(i)))
            a_rules = solution.xpath('{}/fareDetails/productFare/afterSaleRules/text()'.format(package_pre.format(i)))
            w_rules = solution.xpath('{}/fareDetails/productFare/webSalesConditions/text()'.format(
                package_pre.format(i)))
            fare_names = solution.xpath('{}/fareDetails/productFare/fareName/text()'.format(package_pre.format(i)))
            sale_rules = self.rules_join(self.split_rules(s_rules))
            after_sale_rules = self.rules_join(self.split_rules(a_rules))
            web_sales_conditions = self.rules_join(self.split_rules(w_rules))
            seat_type = "_".join([train_dict[i]] * self._len)
            real_class = self.class_join(self.split_rules(passage_type))
            train_corps = self.corp_join(self.split_rules(f_names))
            names = self.equip_json(trains, train_corps)
            train_corp = self.corp_join(self.split_rules(names))
            zip_len = len(prices)
            if train_corp == []:
                for i in range(zip_len):
                    train_corp.append('NULL')
            if web_sales_conditions == []:
                for i in range(zip_len):
                    web_sales_conditions.append('')
            for price, fare_id, printing, r_class, t_corp, s_rule, a_s_rule, w_s_c_rule, f_name in zip(
                    prices,
                    package_fare_id,
                    printing_options_applicable,
                    real_class, train_corp,
                    sale_rules,
                    after_sale_rules,
                    web_sales_conditions,
                    fare_names,
            ):
                printings = printing.xpath('string/text()')
                ticket.append([price, fare_id, printings, r_class,
                               t_corp, seat_type, s_rule, a_s_rule,
                               w_s_c_rule, f_name])
        all_ticket.append(ticket)
        return all_ticket

    def parse_trains(self, req, resp):
        root = etree.fromstring(resp.encode('utf-8'))
        self.solutionid_num = resp.count("/solutionId")
        solutions = self.get_solution(root)
        others_info = dict()
        ticket_list = list()
        offer_count = 0
        redis_key = 'NULL'
        trainnumber = ""
        tmp_paycode = []
        if hasattr(self.task, 'redis_key'):
            redis_key = self.task.redis_key
        train = Train()
        for solution in solutions:
            train.tax = 0
            train.promotion = "NULL"
            train.source = "raileuropeApi"
            train.currency = 'EUR'
            train.change_rule = 'NULL'
            _segments = self.get_segment(solution)
            for segments in _segments:
                segments = segments.xpath('.//segment')
                train.train_no = self.tra_join(segments)
                self.equip_list(segments)
                train.train_type = "_".join(['NULL'] * self.len_seg(segments))
                train.stopid = self.seg_join(segments)
                train.dept_id = train.stopid.split('_')[0]
                train.dest_id = train.stopid.split('_')[-1]
                _city = self.city_code(segments).split('_')
                if len(_city) > 2:
                    all_city = self.split_city(_city)
                if len(_city) == 2:
                    all_city = _city
                train.dept_city = self._from
                train.dest_city = self._to
                train.stop = int(self.len_seg(segments)) - 1
                train.stoptime = self.time_join(segments)
                train.dept_day = train.stoptime[:10]
                train.dept_time = train.stoptime[:19]
                train.dest_time = train.stoptime[-19:]
                train.dur = int(solution.xpath("tripDurationMinutes/text()")[0]) * 60
                train.daydiff = self.diff_join(self.time_join(segments))
            packages = self.get_package(segments, solution)
            for package in packages[0]:
                rules = list()
                _real_class = package[3].split('|')
                fare_name = package[9]
                sale_rule = package[6]
                after_sale_rule = package[7]
                web_sales_conditions = package[8]
                if len(all_city) >= 2 and isinstance(all_city[0], list):
                    for i in range(len(all_city)):
                        return_rule = ("{}到{}段："
                                       "<br/>票价类型：{}（{}）<br/>"
                                       "<br/>购买及使用规则：{}<br/>"
                                       "<br/>退改规则：{}<br/>"
                                       "<br/>线上购买说明：{}<br/><br/>".format(all_city[i][0], all_city[i][1],
                                                                         fare_name, _real_class[0], sale_rule,
                                                                         after_sale_rule, web_sales_conditions))

                        rules.append(return_rule)
                    train.return_rule = "".join(rules)
                else:
                    train.return_rule = ("{}到{}段："
                                         "<br/>票价类型：{}（{}）<br/>"
                                         "<br/>购买及使用规则：{}<br/>"
                                         "<br/>退改规则：{}<br/>"
                                         "<br/>线上购买说明：{}<br/><br/>".format(all_city[0], all_city[1], fare_name,
                                                                           package[3], sale_rule, after_sale_rule,
                                                                           web_sales_conditions))
                train.price = str(float(package[0])/int(self.task.ticket_info.get('v_count', 2)))
                train.real_class = self.real_join(package[3])
                train.train_corp = package[4]
                train.seat_type = package[5]
                train.ticket_type = "NULL"
                paycode = package[1]
                tmp_paycode.append(paycode)
                printing = package[2]
                others_info['paykey'] = {'redis_key': redis_key, 'id': offer_count}
                others_info['payKey'] = {'redis_key': redis_key, 'id': offer_count}
                others_info['printing'] = printing
                others_info['rate_key'] = paycode
                others_info['count'] = self.task.ticket_info.get('v_count', 2)
                offer_count += 1
                train.others_info = json.dumps(others_info)
                ticket_list.append(train.to_tuple())
            self.trainrequest = "true"
            self.trainnumber = trainnumber
            self.dept_time = train.dept_time
        return ticket_list


if __name__ == '__main__':
    task = Task()
    # task.content = "10001&FRPAR&10002&ITRMA&20180427"
    # task.content = "10001&FRPAR&10048&FRLYS&20180414"
    # task.content = "10001&FRPAR&10048&GBLON&20180414"
    # task.content = "10001&FRLYS&10048&GBLON&20180414"
    task.content = "10022&DECGN&10011&CSPRG&20180414"
    task.other_info = {}
    task.ticket_info = {"v_count": 1}
                        # "dept_time": "20180314_12:00"}
    spider = Re4aRailSpider(task)
    result = spider.crawl()
    print result, spider.result

