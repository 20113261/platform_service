#!/usr/bin/env python
# -*- coding: utf-8 -*-
# coding: utf-8

import sys
import hashlib
import json
import requests
import datetime
reload(sys)
sys.setdefaultencoding("utf-8")

__author__ = 'fan bowen'

"""
调用API 时需要对请求参数进行签名验证，服务器也会对该请求参数进行验证是否合法的。方法如下：
如何签名？
签名参数串排序
签名时，根据参数名称，按照字母先后顺序排序：key + value .... key + value 。
注意：
排序若首字母相同，则对第二个字母进行排序，以此类推。
value无需编码，数组类型直接拼接在一起。例如：将“foo=1,bar=2,baz=三”排序为“bar=2,baz=三,foo=1”参数名和参数值链接后，得到拼装字符串bar2baz3foo1。
如果某个字段是字符串，只有是null的时候才不会参加签名，空字符串会被计入签名
签名算法
将分配的得到的密钥（CorperationsSecret）同时拼接到参数字符串头、尾部进行md5Hex加密，再转化成大写，
格式是：md5(CorperationsSecretkey1value1key2value2...CorperationsSecret)。
"""


class HuizucheApi(object):
    def __init__(self, base_url="http://zj.open.api.huizuche.com",
                 requestor='mioji_api', secret='jimiao', redis_key=None, **kwargs):
        super(HuizucheApi, self).__init__(**kwargs)
        self.base_url = base_url
        self.requestor = requestor
        self.secret = secret

        self.redis_key = redis_key
        self.count = 0

    @staticmethod
    def join_keyword(ls, keyword, join_sign):
        """
        提取一个形状如[{'a': 1, 'b': 2}, {'a': 2, 'b': 3}] 返回拼接好的字符串
        :param keyword: 你所要提取的keyword 形如 'a' list: 待提取的list join_sign:分隔符
        :return: 拼接好的字符串 形如 '1,2'
        """
        temp = []
        if not isinstance(ls, list):
            return ''
        for i in ls:
            temp.append(i[keyword])
        return join_sign.join(str(d) for d in temp)

    @staticmethod
    def listilize_keyword(ls, keyword):
        ret = []
        if not isinstance(ls, list):
            return ret
        for i in ls:
            ret.append(i[keyword])
        return ret

    def md5_key(self, req_dict):
        """
        生成md5,先做大写后MD5
        :param req_dict: 存放的参数的dict
        :return: MD5码
        """
        dic = sorted(req_dict.iteritems(), key=lambda d: d[0])  # 转为有序dict
        str_md5 = ''
        for i in dic:
            str_md5 += str(i[0]) + str(i[1])
        m = hashlib.md5()
        str_md5 = self.secret + str_md5 + self.secret
        m.update(str_md5.upper())
        return_str = m.hexdigest()
        return return_str

    def get_json(self, req_dict):
        """
        获取解析后的json数据
        :param req_dict: 请求参数字典
        :return: 返回转化为dict的json数据
        """
        header = self.req_post_header(req_dict)
        api_ret = requests.post(self.base_url, json=req_dict, headers=header).content  # 请求返回一个json值，接下来的是解析
        return_dict = json.loads(api_ret)
        return return_dict

    def run(self, req_dict):
        """
        运行函数
        :param req_dict: 请求参数字典
        :return: 解析后的字典值 形如[{}, {}, {}] 每个{}中都是一个套餐id的结果
        """
        rep = self.get_json(req_dict)
        res = self.analysis_json(rep)
        return res

    def req_post_header(self, req_dict):
        """
        生成header
        :param req_dict: 存放参数的dict
        :return: header
        """
        header = {
            'Content-Type': 'application/json',
            'RequestorCode': self.requestor,
            'RequestorIP': '36.110.118.57',
            'MessageId': 'fbw',
            'Sign': self.md5_key(req_dict)
        }
        return header

    @staticmethod
    def analysis_time(operationtimes, day_of_week):
        """
        解析营业时间的字段，即operationTimes
        :param operationtimes: 形如[{},{}]
        :return: str 形如 0：00~23：59
        """
        tmp_dict = {1: 'MON', 2: 'TUE', 3: 'WED', 4: 'THU', 5: 'FRI', 6: 'SAT', 7: 'SUN'}
        # str_list = []
        for i in operationtimes:
            # day = i['day']
            # open_ = i['open']
            # close = i['close']
            # time_str = day + ' ' + open_ + '~' + close
            # str_list.append(time_str)
            if i['day'] == tmp_dict[day_of_week]:
                val = i['open'] + '~' + i['close']
                if val == '~':
                    return '0:00~23:59'
                return i['open'] + '~' + i['close']

        # return ','.join(str_list)


    @staticmethod
    def cmp_for_cost_list(a, b):
        order_dict = {}

    def analysis_json(self, rep):
        """
        解析网站返回的json
        :param rep: json.loads后的数据
        :return: 解析后的字典值 形如[{}, {}, {}] 每个{}中都是一个套餐id的结果
        """

        res_list = []
        shopVendors = rep['data']['shopVendors'] if isinstance(rep['data']['shopVendors'], list) else []
        pay_key_id = 0
        for shop in shopVendors:
            all_car_inf = shop['vehShops'][0]
            for car_inf in all_car_inf['vehicleCores']:
                res_dict = {}
                start_day = rep['data']['pickupDateTime']
                return_day = rep['data']['returnDateTime']
                start_day = datetime.datetime.strptime(start_day, '%Y-%m-%dT%H:%M:%S')
                return_day = datetime.datetime.strptime(return_day, '%Y-%m-%dT%H:%M:%S')

                #  get借车
                res_dict['get_date'] = start_day.strftime("%Y%m%d")  # 借车点信息
                res_dict['get_time'] = start_day.strftime("%H:%M")
                res_dict['get_week'] = start_day.weekday() + 1
                res_dict['get_open'] = self.analysis_time(all_car_inf['pickupShop']['operationTimes'], res_dict['get_week'])
                res_dict['get_store_name'] = all_car_inf['pickupShop']['locationName']
                res_dict['get_store_traffic'] = all_car_inf['pickupShop']['convenienceLabel']
                res_dict['get_addr'] = all_car_inf['pickupShop']['streetNmbr']
                res_dict['get_tel'] = all_car_inf['pickupShop']['phone']
                res_dict['get_coord'] = str(all_car_inf['pickupShop'].get('longitude', 'None')) + ',' + str(all_car_inf['pickupShop'].get('latitude', 'None'))
                # ---

                #  return还车
                res_dict['return_date'] = return_day.strftime("%Y%m%d")  # 还车点信息
                res_dict['return_time'] = return_day.strftime("%H:%M")
                res_dict['return_week'] = return_day.weekday() + 1
                res_dict['return_open'] = self.analysis_time(all_car_inf['returnShop']['operationTimes'], res_dict['return_week'])
                res_dict['return_store_name'] = all_car_inf['returnShop']['locationName']
                res_dict['return_store_traffic'] = all_car_inf['returnShop']['convenienceLabel']
                res_dict['return_addr'] = all_car_inf['returnShop']['streetNmbr']
                res_dict['return_tel'] = all_car_inf['returnShop']['phone']
                res_dict['return_coord'] = str(all_car_inf['returnShop'].get('longitude', 'None')) + ',' + str(all_car_inf['returnShop'].get('latitude', 'None'))
                #  ---

                # 套餐信息
                res_dict['id'] = car_inf['reference'].get('referenceId', 'None')
                res_dict['name'] = car_inf['reference'].get('packageName', 'None') + '(' \
                    + car_inf['vehPackage'].get('name', 'None') + ')'

                res_dict['fuel'] = {
                    'title': car_inf['vehicle'].get('fuelPolicy', {}).get('desc', 'None'),
                    'desc': '取车时油箱是满的，还车时要加满油' if car_inf['vehicle'].get('fuelPolicy', {}).get('type', 'None') == 'FULLFULL' else '取车时送满箱燃油，还车时不用再加油'
                }
                # 整理policy
                res_dict['policy'] = []
                #  不要的  预付礼遇
                if car_inf.get('promotionPolicys', []):
                    for promotion in car_inf['promotionPolicys']:
                        if 'name' in promotion and 'desc' in promotion:
                            if res_dict['fuel']['title'] in promotion['name']:
                                continue
                            if promotion['name'] != u'副驾名额':
                                continue
                            local_promotion = {
                                'title': promotion['name'],
                                'desc': promotion['desc']
                            }
                            res_dict['policy'].append(local_promotion)
                # if 'name' in car_inf['vehPackage'] and 'desc' in car_inf['vehPackage']:
                #     policy_titles.append(car_inf['vehPackage']['name'])
                #     policy_descs.append(car_inf['vehPackage']['desc'])

                # if car_inf['vehPackage'].get('vehPackageItems', []):
                #     for package in car_inf['vehPackage']['vehPackageItems']:
                #         if 'name' in package and 'desc' in package:
                #             if res_dict['fuel']['title'] in package['name']:
                #                 continue
                #             local_promotion = {
                #                 'title': package['name'],
                #                 'desc': package['desc']
                #             }
                #             res_dict['policy'].append(local_promotion)

                res_dict['insure'] = []
                for ins in car_inf['pricedCoverages']:
                    res_dict['insure'].append(
                        {
                            'name': ins['name'],
                            'code': ins['code'],
                            'excess': "" if not ins['excess'] else ins['excess'],
                            'desc': ins['desc']
                        }
                    )
                #  ---

                #  驾照要求
                res_dict['licence'] = []
                for i in shop['vendor'].get('licenseCombinations'):
                    res_dict['licence'].append(
                        {
                            'name': self.join_keyword(i['driverLicenses'], 'name', '+'),
                            'desc': i['desc']
                        }
                    )
                #  ---

                #  取消政策
                # cancel: json对象 取消政策
                # title: string 政策
                # desc: string 政策描述
                res_dict['取消政策_name'] = car_inf['vehicle'].get('cancellationPolicies', {}).get('name', None)
                res_dict['取消政策_desc'] = car_inf['vehicle'].get('cancellationPolicies', {}).get('desc', None)
                #  ---
                res_dict['tax'] = 0
                res_dict['ccy'] = car_inf['chargeCore']['payableCharge']['chargeCNY']['currency']
                res_dict['val'] = car_inf['chargeCore']['payableCharge']['chargeCNY']['amount']
                res_dict['price_RMB'] = car_inf['chargeCore']['payableCharge']['chargeCNY']['amount']

                # 此处添加如果 本地货币和 人民币都为0则丢弃此条消息
                try:
                    if int(res_dict['val']) == 0 and int(res_dict['price_RMB']) == 0:
                        continue
                    else:
                        pass
                except Exception as why:
                    pass
                # ---------

                #  其他信息
                res_dict['供应商ID'] = shop['vendor'].get('name', 'None')
                res_dict['供应商logo'] = shop['vendor'].get('logo', 'None')
                res_dict['供应商具体描述'] = shop['vendor'].get('desc', 'None')
                res_dict['源名称'] = '惠租车'
                res_dict['carid'] = car_inf['vehicle']['carGroupType']  # 如何匹配ID？
                res_dict['cargroupid'] = car_inf['vehicle']['carGroupCode']
                bandname = car_inf['vehicle'].get('brandName', '') + ' ' + car_inf['vehicle'].get('carName', '')
                bandnameE = car_inf['vehicle'].get('brandNameE', '') + ' ' + car_inf['vehicle'].get('carNameE', '')
                if bandname != ' ' and bandnameE != ' ':
                    band = bandname
                elif bandname != ' ' and bandnameE == ' ':
                    band = bandname
                else:
                    band = bandnameE
                res_dict['car'] = band
                res_dict['similar'] = car_inf['vehicle']['carDesc']
                res_dict['车辆图片'] = car_inf['vehicle'].get('logo_L', '')
                res_dict['t'] = 2 if str(car_inf['vehicle'].get('transmissionType', '')) == 'Manual' else 1
                res_dict['seat'] = car_inf['vehicle'].get('passengerQuantity', '未说明')
                res_dict['door'] = car_inf['vehicle'].get('doors', '未说明')
                res_dict['luggage'] = '{}大{}小行李'.format(
                    car_inf['vehicle'].get('baggageQuantity', ''),
                    car_inf['vehicle'].get('smallBaggageQuantity', '')
                )
                res_dict['desc'] = car_inf['vehicle'].get('spaceDesc', 'None')

                if 'chargeCore' in car_inf and 'rentalQuantity' in car_inf['chargeCore']:
                    res_dict['day'] = car_inf['chargeCore']['rentalQuantity']
                else:
                    if_over_24hour = (return_day - start_day).seconds  # 此处判断的原因是超过二十四小时就算一天
                    day = (return_day - start_day).days
                    if if_over_24hour:
                        day += 1
                    res_dict['day'] = day

                res_dict['distance'] = 1 if car_inf['chargeCore'].get('rateDistance', {}).get('unlimited', '') else 0
                res_dict['distancedesc'] = car_inf['chargeCore'].get('rateDistance', {}).get('quantity', ' ') \
                        + car_inf['chargeCore'].get('rateDistance', {}).get('distUnitName', ' ') if not res_dict['distance'] else None

                try:
                    paymentMode = int(car_inf['chargeCore']['paymentMode'])
                    if paymentMode == 2:
                        res_dict['payment'] = 0
                    elif paymentMode == 3:
                        res_dict['payment'] = 2
                    else:
                        res_dict['payment'] = 1
                except Exception as e:
                    res_dict['payment'] = 'None'
                res_dict['confirm'] = 0

                # Cost 构造
                res_dict['cost'] = self.listilize_keyword(car_inf.get('fees', {}), 'name')
                res_dict['cost'].append(u'税费')
                res_dict['cost'] += self.listilize_keyword(car_inf.get('pricedCoverages', {}), 'name')
                res_dict['cost'] += self.listilize_keyword(car_inf.get('Equipment', {}), 'name')
                # 【'无限里程' or ''】
                if res_dict['distance']:
                    res_dict['cost'].append(u'无限里程')
                else:
                    res_dict['cost'].append(u'限' + res_dict['distancedesc'])

                zuche = {
                    'source': 'huizuche',
                    'car': res_dict['car'],
                    'carId': res_dict['carid'],
                    'cargroupid': res_dict['cargroupid'],
                    'carPic': res_dict['车辆图片'],
                    'similar': res_dict['similar'],
                    't': int(res_dict['t']),
                    'seat': int(res_dict['seat']),
                    'door': int(res_dict['door']),
                    'luggage': res_dict['luggage'],
                    'desc': res_dict['desc'],
                    'price': res_dict['price_RMB'],
                    'realPrice': {
                        'ccy': res_dict['ccy'],
                        'tax': res_dict['tax'],
                        'val': res_dict['val']
                    },
                    'corp': {
                        'id': res_dict['供应商ID'],
                        'desc': res_dict['供应商具体描述']
                    },
                    'day': res_dict['day'],
                    'payment': res_dict['payment'],
                    'get': {
                        'date': res_dict['get_date'],
                        'time': res_dict['get_time'],
                        'week': res_dict['get_week'],
                        'name': res_dict['get_store_name'],
                        'position': res_dict['get_store_traffic'],
                        'addr': res_dict['get_addr'],
                        'tel': res_dict['get_tel'],
                        'open': res_dict['get_open'],
                        'coordinate': res_dict['get_coord']
                    },
                    'return': {
                        'date': res_dict['return_date'],
                        'time': res_dict['return_time'],
                        'week': res_dict['return_week'],
                        'name': res_dict['return_store_name'],
                        'position': res_dict['return_store_traffic'],
                        'addr': res_dict['return_addr'],
                        'tel': res_dict['return_tel'],
                        'open': res_dict['return_open'],
                        'coordinate': res_dict['return_coord']
                    },
                    'set': {
                        'name': res_dict['name'],
                        'id': res_dict['id'],
                        'policy': res_dict['policy'],
                        'cost': res_dict['cost'],
                        'insure': res_dict['insure'],
                        'fuel': res_dict['fuel'],
                        'distance': {
                            'desc': res_dict['distancedesc']
                        },
                        'cancel': {
                            'title': res_dict['取消政策_name'],
                            'desc': res_dict['取消政策_desc']
                        }
                    },
                    'licence': res_dict['licence'],
                    "paykey": {
                        "redis_key": self.redis_key,
                        "id": pay_key_id,
                    }
                }
                res_list.append(zuche)
                pay_key_id += 1
        return res_list


if __name__ == '__main__':
    api = HuizucheApi()
    post = {
        'pickupDateTime': '2017-12-22T10:00:00',
        'returnDateTime': '2017-12-23T10:00:00',
        'pickupLocationCode': 'LAX',
        'returnLocationCode': 'LAX',
    }
    api.run(post)
