#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import base64
import datetime
import re
import sys
import urlparse

from mioji.common.utils import setdefaultencoding_utf8
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_NEVER
from mioji.common.check_book.check_book_ratio import use_record_qid

setdefaultencoding_utf8()
if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')
default_encoding = sys.getdefaultencoding()


class zuzucheSpider(Spider):
    source_type = 'zuzuche'
    targets = {
        'Car': {}
    }
    old_spider_tag = {
        "zuzucheCar": {"required": ["Car"]}
    }

    def __init__(self, task=None):
        Spider.__init__(self, task=task)
        # 任务信息
        self.header = {}
        self.f_url = 'standard/queryQuote.php'
        # self.f_url = 'http://test.api.zuzuche.com/2.0/'
        self.url = ''
        self.auth_str = ''
        self.params = {}
        self.redis_key = self.task.redis_key if hasattr(self.task, 'redis_key') else 'Null'

    def targets_request(self):
        if self.task is None:
            raise parser_except.ParserException(parser_except.TASK_ERROR, '没传task进来')
        self.get_requests_data()
        use_record_qid(unionKey='zuzucheApi', api_name="queryQuote.php", task=self.task, record_tuple=[1, 0, 0])

        @request(retry_count=1, proxy_type=PROXY_NEVER, binding=self.parse_Car)
        def make_request():
            return {
                'req': {
                    'method': 'GET',
                    'url': self.url,
                    'headers': self.header,
                    'params': self.params
                },
                'data': {'content_type': 'json'},
            }
        return [make_request]

    def get_requests_data(self):
        auth_info = json.loads(self.task.ticket_info.get('auth', '{}'))
        base_url = auth_info.get('url')
        username = auth_info.get('username')
        password = auth_info.get('password')
        if not base_url or not username or not password:
            raise parser_except.ParserException(121, '无认证信息')
        if not base_url.endswith('/'):
            base_url += '/'
        self.url = urlparse.urljoin(base_url, self.f_url)
        self.auth_str = base64.b64encode(username + ':' + password)
        self.pay_key = 'Null'
        if hasattr(self.task, 'redis_key'):
            self.pay_key = self.task.redis_key
        rent_info = self.task.ticket_info['zuche']
        self.params = self.get_params(rent_info)
        self.header = {'Authorization': self.auth_str}

    def get_params(self, zuche_info):
        pickupDate, pickupDateTime = zuche_info['pickupDateTime'].split('T')
        dropoffDate, dropoffDateTime = zuche_info['returnDateTime'].split('T')
        pickupLocationCode = zuche_info['pickupLocationCode']
        returnLocationCode = zuche_info['returnLocationCode']
        pt = zuche_info.get('pt', '1')
        other_keywords = {
            't': zuche_info.get('t') ,   # 车型组
            'tr': zuche_info.get('tr'),  # 排挡
            's': zuche_info.get('s'),    # 座位
            'di': zuche_info.get('di'),  # 供应商
        }
        base_data = {
            'pt': pt,   # 预付全额
            'pickupDate': pickupDate,
            'dropoffDate': dropoffDate,
            'pickupDateTime': pickupDateTime,
            'dropoffDateTime': dropoffDateTime,
        }
        if pickupLocationCode.isalpha():
            # 查询格式为机场三字码
            base_data['type'] = '1'
            base_data['pickupIATA'] = pickupLocationCode
            base_data['dropoffIATA'] = returnLocationCode
        else:
            # 通过坐标查询
            base_data['type'] = '6'
            base_data['pickupCoordinate'] = pickupLocationCode
            base_data['dropoffCoordinate'] = returnLocationCode
        for i in other_keywords:
            if other_keywords[i]:
                base_data[i] = other_keywords[i]
        return base_data

    def response_error(self, req, resp, error):
        # 目前测试403为认证信息错误所返回code
        if error.response.status_code == 401 and "AUTH_FALSE" in error.response.content:
            raise parser_except.ParserException(122, '认证信息错误')

    def parse_Car(self, req, resp):
        if not resp['success']:
            if '所搜索的报价信息不存在' in resp['text']:
                raise parser_except.ParserException(parser_except.EMPTY_TICKET, resp['text'])
            raise parser_except.ParserException(parser_except.UNKNOWN_ERROR, resp['text'])
        else:
            result = []
            pay_key_id = 0
            # i 代表车型组
            for i in resp['data']['vehicles']:
                # j 代表这个车型组下拥有的由不同公司提供的套餐, 也代表了不同的报价
                for j in i['supplierQuotes']:
                    # k 代表了每个具体的套餐
                    for k in j['allQuotes']:
                        # 车型id
                        type_id = i['vehicleInfo']['vehicleTypeId']

                        zuche = {}
                        costs = list(set([cost['name'] for cost in k['priceIncludes']]))
                        zuche['carId'] = get_car_type(resp['data']['vehicleTypeDescs'][str(type_id)]['vehicleName']) + u''
                        zuche['car'] = i['vehicleInfo']['vehicleName']
                        zuche['cargroupid'] = i['vehicleInfo']['sipp']
                        zuche['source'] = 'zuzuche'
                        zuche['carPic'] = i['vehicleInfo']['imagePath']
                        zuche['similar']= resp['data']['vehicleTypeDescs'][str(type_id)]['reference']
                        # 国际车型代码： 四个大写英文字母
                        zuche['t']= 1 if i['vehicleInfo'][u'transmission'] == '自动挡' else 2
                        # 租租车返回的座位比较精确，需要和现有逻辑（<5，>=5）统一？
                        zuche['seat']= i['vehicleInfo']['seat']
                        zuche['door']= i['vehicleInfo']['door']
                        zuche['luggage']= resp['data']['vehicleTypeDescs'][str(type_id)]['bag']
                        zuche['desc'] = re.sub(r'<p>|</p>', '', resp['data']['vehicleTypeDescs'][str(type_id)]['totalTips'])
                        zuche['price'] = k['priceInfo']['totalPriceRMB']
                        zuche['realPrice'] = {
                            # 租租车必定会返回CNY的报价，所以默认取CNY
                            'ccy': 'CNY',
                            # 只能确定是否包含税费，但不能得到税费具体数值
                            'tax': .0,
                            # 只能得到总价，无法得到不包含税的价格
                            'val': k['priceInfo']['totalPriceRMB']
                        }
                        zuche['corp'] = {
                            # 我方的供应商id映射
                            'id': supplier_mapping(resp['data']['suppliers'][str(j['supplierId'])]['supplierName']),
                            'desc': '',
                            # 'logo': resp['data']['suppliers'][str(j['supplierId'])]['supplierImage']
                        }

                        zuche['day'] = resp['data']['rentInfo']['days']

                        payment_type = k['priceInfo']['paymentType']
                        payment_map = {
                            'prepaid': 0,
                            'postpaid': 1,
                            'partpaid': 2
                        }
                        zuche['payment'] = payment_map[payment_type]

                        pick_up_store_id = j['pickupStoreId']
                        if pick_up_store_id == 0:
                            # 未知 bug 门店为0， 跳过
                            break
                        pick_up_addr_store_key = str(j['supplierId']) + '_' + str(pick_up_store_id)
                        zuche['get'] = {
                            'date': str(resp['data']['rentInfo']['pickupDate']).replace('-', ''),
                            'time': resp['data']['rentInfo']['pickupTime'],
                            'week': datetime.datetime.strptime(resp['data']['rentInfo']['pickupDate'],
                                                                '%Y-%m-%d').weekday() + 1,
                            'addr': resp['data']['locations'][pick_up_addr_store_key].get('address'),
                            'position': resp['data']['locations'][pick_up_addr_store_key].get('howToReach').replace('门店位于',''),
                            # 租租车接口的返回结果没有门店电话
                            'tel': '',
                            'open': resp['data']['locations'][pick_up_addr_store_key].get('openTime', ''),
                            'coordinate': resp['data']['locations'][pick_up_addr_store_key].get('longitude', '')
                                     + ',' +resp['data']['locations'][pick_up_addr_store_key].get('latitude'),
                            'name': resp['data']['locations'][pick_up_addr_store_key].get('locationName')
                        }
                        drop_off_store_id = j['dropoffStoreId']
                        drop_off_addr_store_key = str(j['supplierId']) + '_' + str(drop_off_store_id)
                        zuche['return'] = {
                            'date': str(resp['data']['rentInfo']['dropoffDate']).replace('-', ''),
                            'time': resp['data']['rentInfo']['dropoffTime'],
                            'week': datetime.datetime.strptime(resp['data']['rentInfo']['dropoffDate'],
                                                               '%Y-%m-%d').weekday() + 1,
                            'addr': resp['data']['locations'][drop_off_addr_store_key].get('address'),
                            'position': resp['data']['locations'][drop_off_addr_store_key].get('howToReach').replace('门店位于',''),
                            # 租租车接口的返回结果没有门店电话
                            'tel': '',
                            'open': resp['data']['locations'][drop_off_addr_store_key].get('openTime', ''),
                            'coordinate': resp['data']['locations'][drop_off_addr_store_key].get('longitude', '')
                                     + ',' + resp['data']['locations'][drop_off_addr_store_key].get('latitude'),
                            'name': resp['data']['locations'][drop_off_addr_store_key].get('locationName')
                        }
                        fuel_policy = k['fuelPolicy']
                        # print k['insuranceType']
                        # 这个字段的大部分信息都在"附录查询"（API -7）的接口
                        # 那个接口包含 "保险说明、驾照要求、订单条款、租车须知"
                        insuranceType_map = {'complete': u'全险', 'strong': u'加强险', 'base': u'基本险'}
                        insure_name = k.get('packageName0').split('（')[0] if '（' in k.get('packageName0') else ''

                        zuche['set'] = {
                            # 没有名字
                            'spec': [1,2], # 退改相关
                            'name': insure_name or insuranceType_map.get(k['insuranceType']) or k['insuranceType'],
                            # 车辆报价id
                            'id': k['id'],
                            'policy': [],
                            'cost': costs,
                            'insure': insure_map.get(insure_name, []),
                            'fuel': {
                                'title': resp['data']['fuelPolicyTips'][fuel_policy]['policyTitle'],
                                'desc': resp['data']['fuelPolicyTips'][fuel_policy]['content']
                            },
                            'cancel': {'desc': '','title': ''},   # 需要打第二个接口
                            'distance': {
                                'desc': u'无里程限制' if u'无里程限制' in costs else u''
                            }
                        }
                        if '（' in k.get('packageName1'):
                            pl_title, pl_desc = k.get('packageName1', '').split('（', 1)
                            zuche['set']['policy'].append({'title': pl_title, 'desc': pl_desc.replace('）', '')})

                        license_includes = k['driverLicenseSupportId']
                        all_licenses = [resp['data']['driverLicenseSupportDesc'][li].split('<font class=caa>（') for li in license_includes]
                        zuche['licence'] = [{'name': title, 'desc': desc.replace('）</font>', '')} for title, desc in all_licenses]
                        # 租租车接口没有这个字段
                        zuche['paykey'] = {
                            "redis_key": self.redis_key,
                            "id": pay_key_id,
                        }
                        pay_key_id += 1
                        result.append(zuche)
                        # res.append((k.get('packageName1'), k.get('packageName0'), zuche['set']['name'], zuche['set']['id']))
        # for a, b, c, d in res:
        #     print a, b, c, d
        return result

# res = []
our_supplier = [u'Hertz',u'Dollar',u'Thrifty',u'Alamo',u'National',u'Enterprise',u'Budget',u'Avis',u'Europcar',u'Sixt',
                u'East Coast Rentals',u'Buchbinder''Global Drive',u'Megadrive',u'National Thai',u'Peel',u'Greenmotion',
                u'Bargain Car Rentals',u'Jucy',u'Bizcar Rental',u'Thai Rent A car',u'QQ Car Rental',u'KX Rent A Car',
                u'Discount Car Rentals',u'Geelong',u'Nzirental',u'SCCR',u'Jace Car Rental',u'Chic Car Rent',u'TWDR',
                u'AO Car Rental',u'Paradise''Fox']

i_our_supplier = [x.lower() for x in our_supplier]

insure_map = {
    u'全额险': [{
        'desc': u'保车辆碰撞/被盗抢造成的损失',
        'code': u'LDW_0',
        'name': u'碰撞险 盗抢险',
        'excess': u'起赔额为0元',
    }],
    u'基本险': [{
        'desc': u'保车辆碰撞/被盗抢造成的损失',
        'code': u'LDW_0',
        'name': u'碰撞险 盗抢险',
        'excess': u'有起赔额'
    }],
    u'综合全险':[{
        'desc': u'保车辆碰撞/被盗抢造成的损失',
        'code': u'LDW_0',
        'name': u'碰撞险 盗抢险',
        'excess': u'起赔额为0元'
    },{
        'desc': u'致使第三者遭受人身伤亡，可获得保险公司赔偿',
        'code': u'ALI',
        'name': u'第三者险',
        'excess': u'最高100万美元'
    }],
    u'超级全险':[{
        'desc': u'保车辆碰撞/被盗抢造成的损失',
        'code': u'LDW_0',
        'name': u'碰撞险 盗抢险',
        'excess': u'起赔额为0元'
    },{
        'desc': u'致使第三者遭受人身伤亡，可获得保险公司赔偿',
        'code': u'ALI',
        'name': u'第三者险',
        'excess': u'最高100万美元'
    },{
        'desc': u'保车内人员意外伤害损失',
        'code': u'PAI',
        'name': u'人身险',
        'excess': u'',
    },{
        'desc': u'减少车内个人财物丢失的损失',
        'code': u'PEC',
        'name': u'财务险',
        'excess': u''
    }],
    u'特惠超级全险':[{
        'desc': u'保车辆碰撞/被盗抢造成的损失',
        'code': u'LDW_0',
        'name': u'碰撞险 盗抢险',
        'excess': u'起赔额为0元'
    },{
        'desc': u'致使第三者遭受人身伤亡，可获得保险公司赔偿',
        'code': u'ALI',
        'name': u'第三者险',
        'excess': u'最高100万美元'
    },{
        'desc': u'承担道路故障的救援费、拖车费、人工费',
        'code': u'',
        'name': u'道路救援',
        'excess': u'',
    },{
        'desc': u'租车公司的车险一般不保',
        'code': u'',
        'name': u'车辆玻璃、轮胎、底盘破损',
        'excess': u''
    },{
        'desc': u'承担客观原因导致旅行取消的租车费用损失',
        'code': u'',
        'name': u'旅行取消',
        'excess': u''
    }]
}


def supplier_mapping(supplier):
    if supplier.lower() in i_our_supplier:
        return our_supplier[i_our_supplier.index(supplier.lower())]
    return supplier


def get_car_type(s):
    if '高级轿车' in s:
        return u'高级车'
    elif 'SUV' in s:
        return u'越野车SUV'
    elif 'MPV' in s:
        return u'商务车MPV'
    elif '旅行车' in s:
        return u'旅行车'
    elif '轿跑' in s or '跑车' in s:
        return u'跑车'
    elif '中' in s:
        return u'中型车'
    tiny = ['微型', '小型', '紧凑型']
    for i in tiny:
        if i in s:
            return u'紧凑型车'
    return u'特殊车型'




if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_http_proxy, simple_get_socks_proxy, httpset_debug

    httpset_debug()

    query = {
        "pickupLocationCode": "LAX",
        "returnLocationCode": "LAX",

        "pickupDateTime": "2018-02-25T18:00:00",
        "returnDateTime": "2018-02-26T08:00:00"
    }
    task = Task()
    auth_str = json.dumps({'username': 'L01130847-TEST', 'password':'TESTfhALO)', 'url': 'http://test.api.zuzuche.com/2.0'})
    task.ticket_info = {'zuche': query,'auth': auth_str, }
    task.other_info = {}
    # task.redis_key = 'asdfasdfasdf'
    spider = zuzucheSpider()
    spider.task = task
    print spider.source_type
    print spider.crawl()
    print spider.result
    # # print spider.browser.resp.text
    # print spider.result
    # print tes
    # for a, b in tes:
    #     print a, b
    # import json, io
    # with io.open('output', 'w', encoding='utf=8') as fp:
    #     tmp = json.dumps(spider.result, indent=2, ensure_ascii=False)
    #     fp.write(tmp)
