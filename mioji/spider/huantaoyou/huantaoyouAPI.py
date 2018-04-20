#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import hashlib
import requests
from mioji.common.logger import logger
from analysis_json import *
from mioji.common import parser_except
from mioji.common.check_book.check_book_ratio import use_record_qid

"""
调用API 时需要对请求参数进行签名验证，服务器也会对该请求参数进行验证是否合法的。方法如下：
根据参数名称（除签名）将所有请求参数按照字母先后顺序排序:key + value .... key + value
例如：将foo=1,bar=2,baz=3 排序为bar=2,baz=3,foo=1，参数名和参数值链接后，得到拼装字符串bar2baz3foo1
将private_key 拼接到参数字符串头、尾进行md5加密后，再转化成大写，格式是：toUpperCase(md5(secretkey1value1key2value2...secret))
ID: 19
KEY: Huantaoyou123456
"""

# 门票 category_id： 3
PRO_TICKET = 3
# 当地美食 category_id: 1
PRO_FOOD = 1
# 休闲娱乐 category_id: 2
PRO_PLAY = 2

class HuantaoyouApi(object):
    """
    使用时先实例化，每个id调用一次type_classification(id)和 api.tickets_fun_analysis(id)方法,其中解析部分有print是为了调试方便以及
    给出case，使用时直接return return_dict即可
    """
    def __init__(self, task=None):
        self.task = task
        try:
            auth = json.loads(task.ticket_info['auth'])
            self.id = auth['channel_id']
            self.key = auth['key']
            self.version = auth['version']
            self.base_url = auth['base_url']
        except Exception as e:
            logger.error(e)
            raise parser_except.ParserException(12, "检查一下task信息")

        self._itinerary_count = 0
        self.val = None
        use_record_qid(unionKey='欢逃游 API', api_name="getItemDetailTotalByID", task=task, record_tuple=[1, 0, 0])

    def getPayKey(self):
        redis_key = self.task.redis_key
        id = self._itinerary_count
        self._itinerary_count += 1
        return {'redis_key': redis_key, 'id': id}

    def search_inf(self):
        req_dict = {}
        req_dict['channel_id'] = self.id
        req_dict['fields'] = 'id,title,book_day,address,category_name,country_name,city_name'
        req_dict['page_no'] = '1'
        req_dict['page_size'] = '200'
        req_dict['status'] = '1'
        req_dict['version'] = self.version
        sign = self.md5_key(req_dict)
        action_url = 'getAllItemList.json?'
        req_url = self.req_url(req_dict, sign, action_url)
        resp = requests.get(req_url)
        api_ret = resp.content
        return api_ret

    def md5_key(self, req_dict):
        """
        生成md5
        :param req_dict: 存放的参数的dict
        :return: MD5码
        """
        dic = sorted(req_dict.iteritems(), key=lambda d: d[0])  # 转为有序dict
        str_md5 = ''
        for i in dic:
            str_md5 += str(i[0]) + str(i[1])
        m = hashlib.md5()
        str_md5 = self.key + str_md5 + self.key
        m.update(str_md5)
        return_str = m.hexdigest()
        return return_str.upper()

    def req_url(self, req_dict, sign, action_url):
        """
        生成url
        :param req_dict: 存放参数的dict
        :param sign: md5
        :param action_url: 请求的网址的动作尾缀如 getAllItemList.json?
        :return: url
        """
        dic = sorted(req_dict.iteritems(), key=lambda d: d[0])
        url = '&'.join([str(x[0]) + '=' + str(x[1]) for x in dic])
        url += '&sign=' + sign
        url = self.base_url + action_url + url
        return url

    def type_classification(self, id, api_ret=None):
        """
        分类函数，把所有id分类筛选出来
        :param id:  景点id
        :return: return 方法
        """
        if not api_ret:
            api_ret = self.get_json(id)

        all_ret = {
            'view_ticket': {},
            'play_ticket': {},
            'activity_ticket': {},
            'tour_ticket': {},
        }
        # 匹配产品类型
        if api_ret['data']['category_id'] == PRO_TICKET:  # 门票类
            all_ret['view_ticket'] = self.view_ticket_analysis(api_ret)

        elif api_ret['data']['category_id'] == PRO_FOOD or api_ret['data']['category_id'] == PRO_PLAY:  # 特色活动类
            ret = self.get_play_ticket(api_ret)
            if not ret:
                all_ret['activity_ticket'] = self.activity_ticket_analysis(api_ret)
            else:
                all_ret['play_ticket'] = ret

        # 判断条件 catename 一日游 或者名字里面半日的问题
        # 不需要一日游、半日游
        # if api_ret['data']['category_name'] == '一日游' or '半日' in api_ret['data']['title'] or '1日' in api_ret['data']['title']:
        #     all_ret['tour_ticket'] = self.tour_ticket_analysis(api_ret)
        self.val = all_ret
        return all_ret

    def get_play_ticket(self, api_resp):
        perform_time = api_resp['data'].get('consumer_remind', {}).get('perform_time', 'None')
        perform_period = api_resp['data'].get('consumer_remind', {}).get('perform_period', 'None')
        if perform_period and perform_time:
            #  这里用两次if判断是为了筛选掉这两个值存在key但是value为空的情况
            if perform_period != 'None' or perform_time != 'None':
                return self.play_ticket_analysis(api_resp)
        return None

    def assert_value(self, resp):
        assert resp['code'] == 0, resp['msg']

    def prepare_request(self, id):
        action_url = 'getItemDetailTotalByID.json?'
        req_dict = {}
        req_dict['channel_id'] = self.id
        req_dict['version'] = self.version
        req_dict['id'] = id
        sign = self.md5_key(req_dict)
        req_url = self.req_url(req_dict, sign, action_url)
        return req_url

    def get_json(self, id):
        req_url = self.prepare_request(id)
        api_ret = requests.get(req_url).content  # 请求返回一个json值，接下来的是解析
        api_ret = json.loads(api_ret)
        self.assert_value(api_ret)
        return api_ret
    '''
    def inn_order(self, req_data):
        action_url = 'orderVerification.json?'
        req_dict = {}
        req_dict['channel_id'] = self.id
        req_dict['version'] = self.version
        req_dict[req_data.split('|')[0]] = req_data.split('|')[1]+'_1803_1_2017-08-11'
        sign = self.md5_key(req_dict)
        req_url = self.req_url(req_dict, sign, action_url)
        return req_url
    '''

    def tickets_fun_analysis(self, id, val=None, api_ret=None):
        if not api_ret:
            api_ret = self.get_json(id)
        if not val:
            val = self.val
        result_dict = tickets_fun_analysis(api_ret, val)
        others_info = {}
        others_info['paykey'] = self.getPayKey()
        payInfo = {}
        payInfo['id'] = api_ret['data']['id']
        payInfo['skuid'] = []
        payInfo['price'] = []
        payInfo['isOrderRemark'] = []
        payInfo['type'] = []
        payInfo['confirmInfo'] = []
        skulist = api_ret['data']['skulist']
        payInfo['need_guest_info'] = api_ret['data']['need_guest_info']
        payInfo['paper_code'] = api_ret['data']['paper_code']
        payInfo['code'] = api_ret['data']['verification']['code']
        payInfo['date'] = self.task.other_info['date']
        for sku in skulist:
            payInfo['skuid'].append(sku['id'])
            payInfo['isOrderRemark'].append(sku['isOrderRemark'])
            payInfo['type'].append(sku['type'])
            payInfo['confirmInfo'].append(sku['confirmInfo'])
            schedule = sku['schedule']
            for sch in schedule:
                payInfo['price'].append(sch['price'])
        others_info['payInfo'] = payInfo
        result_ticket = []
        for dic in result_dict:
            dic['__type'] = 'tickets_fun'
            dic['others_info'] = others_info
            result_ticket.append(dic)
        return result_ticket

    @staticmethod
    def view_ticket_analysis(api_ret):
        result_dict = view_ticket_analysis(api_ret)  #
        result_dict['__type'] = 'view_ticket'
        return result_dict

    @staticmethod
    def play_ticket_analysis(api_ret):
        result_dict = play_ticket_analysis(api_ret)
        result_dict['__type'] = 'play_ticket'
        return result_dict

    @staticmethod
    def activity_ticket_analysis(api_ret):
        result_dict = activity_ticket_analysis(api_ret)
        result_dict['__type'] = 'activity_ticket'
        return result_dict

    @staticmethod
    def tour_ticket_analysis(api_ret):
        result_dict = tour_ticket_analysis(api_ret)
        result_dict['__type'] = 'tour_ticket'
        return result_dict


if __name__ == '__main__':
    api = HuantaoyouApi()
    # print api.search_inf()
    '''
    ids_dict = {
        'view_ticket':[
            10013,
            10006,
            10003,
            10016,
            10021,
            10061,
            10082,
            10085,
            10086,
            10087,
        ],
        'tour_ticket':[
            10028,
            10158,
            10299,
            10301,
            10413,
            10414,
            10422,
            10429,
            10432,
            10445,
        ],
        "activity_ticket": [
            10018,
            10037,
            10038,
            10040,
            10039,
            10042,
            10041,
            10043,
            10046,
            10047,
        ]
    }
    for key, id_list in ids_dict.items():
        print '\n\n\n', key
        for my_id in id_list:
            api_resp = api.get_json(my_id)
            print json.dumps(api.type_classification(my_id, api_resp), indent=2, ensure_ascii=False)
            print json.dumps(api.tickets_fun_analysis(my_id, api_resp), indent=2, ensure_ascii=False)
            pt = api.get_play_ticket(api_resp)
            if pt:
                print json.dumps(pt, indent=2, ensure_ascii=False)
            else:
                print '没法生成play ticket'
            print '\n'
    '''
    api_resp = api.get_json(10018)
    #print json.dumps(api_resp)
    print json.dumps(api.type_classification(10085, api_resp), indent=2, ensure_ascii=False)
    print json.dumps(api.tickets_fun_analysis(10085, api_ret=api_resp), indent=2, ensure_ascii=False)
    #print api.inn_order('sku_count|10128')
    # try:
    #     consumer_terminal = api_resp['data']['consumer_terminal']
    #     print json.dumps(consumer_terminal, indent=2, ensure_ascii=False)
    # except:
    #     print "没有consumer_terminal"
    #     print json.dumps(api_resp, indent=2, ensure_ascii=False)
