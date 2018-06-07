#!/usr/bin/env python
# coding:utf-8

"""
@File: tuniu_parser.py
@License: Private@Mioji
@DevTool: Pycharm-CE 2017 
@Author: WangXinyong
@E-mail: wangxinyong@mioji.com
@Time: 18/2/4 下午6:27
"""

import re
import ast
from pprint import PrettyPrinter
from HTMLParser import HTMLParser, HTMLParseError
from lxml.etree import HTMLParser as LXML_HTMLParser
from xml.etree.ElementTree import fromstring as etree_from_string
from mioji.common.parser_except import ParserException


class BaseModel(object):
    """Model基类，实现Model通用方法"""
    __slots__ = ()

    def to_dict(self):
        result = dict()
        for key in self.__slots__:
            if key.startswith('__'):
                continue
            value = getattr(self, key)
            if key == 'traffic':
                pass
            else:
                if isinstance(value, BaseModel):
                    value = value.to_dict()
                elif isinstance(value, list):
                    value = map(lambda x: x.to_dict() if isinstance(x, BaseModel) else x, value)
                elif isinstance(value, dict):
                    _v = dict()
                    for k,v in enumerate(value):
                        if isinstance(v,BaseModel):
                            _v.update({k:v.to_dict()})
                        else:
                            _v.update({k:v})
                    value = _v
                elif isinstance(value,set):
                    value = map(lambda x: x.to_dict() if isinstance(x, BaseModel) else x, value)
                    value = set(value)
            result[key] = value
        return result

    def to_dict_simple(self):
        return {key: getattr(self, key)
                for key in self.__slots__
                if not key.startswith('__')}

    def show(self):
        p_print = PrettyPrinter(indent=4, depth=3).pprint
        p_print(self.to_dict())


class HotelModel(BaseModel):
    """酒店Model"""
    __slots__ = ('desc', '__plans', 'plans')

    def __init__(self):
        self.desc = ''  # 酒店信息的整体描述
        self.__plans = []  # 参考方案

    @property
    def plans(self):
        return self.__plans

    @plans.setter
    def plans(self, value):
        assert isinstance(value, list)
        for item in value:
            self.add_plans(item)

    def add_plans(self, value):
        assert isinstance(value, dict)
        one_item = dict()
        one_item['name'] = value.get('name', '')  # 酒店名称
        one_item['name_en'] = value.get('name_en', '')  # 酒店英文名
        one_item['addr'] = value.get('addr', '')  # 酒店地址
        one_item['intro'] = value.get('intro', '')  # 酒店简介
        one_item['img'] = value.get('img', [])
        self.__plans.append(one_item)


class RouteModel(BaseModel):
    """行程Model"""
    __slots__ = ('desc', '__citys', 'citys', '__detail', 'detail')

    def __init__(self):
        self.desc = ''  # 本日行程述
        self.__citys = []  # 本日目的地城市
        self.__detail = []  # 行程具体安排

    @property
    def citys(self):
        return self.__citys

    @citys.setter
    def citys(self, value):
        assert isinstance(value, list)
        for item in value:
            self.add_city(item)

    def add_city(self, id='', name=''):
        one_item = dict()
        one_item['id'] = id  # 目的地ID
        one_item['name'] = name  # 目的地名称
        self.__citys.append(one_item)

    @property
    def detail(self):
        return self.__detail

    @detail.setter
    def detail(self, value):
        assert isinstance(value, list)
        for item in value:
            self.add_detail(item)

    def add_detail(self, value):
        assert isinstance(value, dict)
        one_item = dict()
        # 节点类型 0:其他 10:交通 11:飞机 20:景点 21:用餐 22:玩乐 23:自由活动 30:酒店
        one_item['type'] = value.get('type', 0)
        one_item['name'] = value.get('name', '')  # 节点名称
        one_item['stime'] = value.get('stime', '')  # 开始时间 格式hh:mm
        one_item['dur'] = value.get('dur', 0.0)  # 在该节点安排的时长
        one_item['desc'] = value.get('desc', '')  # 对当前节点的描述
        one_item['image_list'] = value.get('image_list', [])  # 图片列表
        self.__detail.append(one_item)


class TourModel(BaseModel):
    """人员类型对应信息Model"""
    __slots__ = ('name', 'price', 'rest', 'age_lower', 'age_upper')

    def __init__(self):
        self.name = ''  # 人员类型名称
        self.price = 0.0  # 价格
        self.rest = 0  # 库存量
        self.age_lower = 0  # 人员年龄下限
        self.age_upper = 11  # 人员年龄上限


class VacationModel(BaseModel):
    """跟团游产品Model"""
    __slots__ = ('child_standard', 'source_type', 'pid', 'pid_3rd', 'first_image', 'sid', 'ccy', 'feature', 'dest', 'dept', 'dept_city',
                 'extra_traffic', 'extra_city', 'name', 'date', 'set_name', 'set_id', 'star_level', 'time', 'highlight',
                 'confirm', 'sell_date_late', 'book_pre', 'tag', 'image_list', 'rec', 'stat', 'hotel', 'expense',
                 'other', 'disable', 'single_room', 'tourist', 'tour_stat', 'ctime', 'route_day', 'is_multi_city',
                 'multi_city', 'ptid', 'traffic')

    def __init__(self):
        self.child_standard = ''
        self.source_type = 'tuniu|vacation'
        self.pid = "gty+yyyMMdd+number"
        self.pid_3rd = ""   # 产品ID
        self.first_image = ""   #self.top_image = ''  # 对应产品头图None
        self.sid = ""   #self.supplier = ''  # 供应商：公司全称
        self.ccy = "CNY"
        self.feature = ""
        self.dest = []
        self.dept = []
        self.dept_city = []
        self.extra_traffic = 0
        self.extra_city = []
        self.name = ""  # 产品名称 OK
        self.date = ""  # 出发日期 OK   #self.start_date = '2018-02-01'  # 启程时间
        self.set_name = "无"  # 套餐名称（线路）OK
        self.set_id = ""  # 套餐ID OK
        self.star_level = 1  # 行程星级 OK
        self.time = 0  # 行程天数（日）OK  self.num_of_days = 1  # 行程天数
        self.highlight = []  # 产品亮点
        self.confirm = 0  # 预定确认方式，默认给0 OK None
        self.sell_date_late = ""  # 最晚可售日期  self.sell_deadline = ''  # 最晚可售日期
        self.book_pre = 0  # 提前预定天数，0表示不限
        self.tag = []  # 特色标签ID 给空 OK None
        self.image_list = []  # 轮播图列表 OK
        self.rec = ""  # 产品经理推荐内容 OK
        self.stat = 0  # 录入审核状态 OK  self.state = 0  # 录入审核状态 参考标注系统-通用字段-标志状态 0
        self.hotel = {"desc": "",
                      "plans": []}  # 参考酒店信息  plans里是这样的{"name": "NULL", "name_en": "NULL", "addr": "NULL", "intro": "NULL", "img": "NULL"}多个字典  OK
        self.expense = [{"type": 0, "title": "", "content": ""}, {"type": 1, "title": "", "content": ""},
                        {"type": 2, "title": "", "content": ""}]  # 费用说明  OK
        self.other = [{"title": "pre_info", "content": ""}, {"title": "visa_info", "content": ""}]  # 其他说明 OK
        self.disable = 0  # OK
        self.single_room = float(0.0)  # 单房差  OK
        self.tourist = []  # 不同人员类型的详细价格和库存，没有可以给空 OK
        self.tour_stat = 0  # 成团状态，0：未成团， 1：已成团 OK
        self.ctime = ""  # 爬取时间戳  OK
        self.route_day = []  # 行程介绍  OK
        # [{"city": {"id": "NULL", "name": "NULL"}, "desc": "NULL", "detail": [{"type": "0", "stime": "NULL", "dur": 0, "name": "NULL", "desc": "NULL", "image_list": []}]}]
        self.is_multi_city = "no"
        self.multi_city = []
        self.ptid = 'ptid'
        self.traffic = {
            'desc': '',
            'plans': []
        }

    def add_expense(self, _type, title, content):
        self.expense.append({
            'type': _type,
            'title': title,
            'content': content
        })

    def add_other(self, value):
        """{'title': title,'content': content}"""
        self.other.append(value)

    def add_route(self, value):
        """传RouteModel实例"""
        assert isinstance(value, RouteModel)
        self.route_day.append(value)

    def add_tour(self, value):
        """添加TourModel实例"""
        assert isinstance(value, TourModel)
        self.tourist.append(value)


class Utils(object):

    @classmethod
    def unescape(cls, src):
        try:
            result = HTMLParser().unescape(src)
        except HTMLParseError as e:
            result = src
        return result

    @classmethod
    def parse_js(cls, expr):
        """
        解析非规则json数据(有一个BUG:Json Bool型value仍是原始字符串)
        """
        try:
            m = ast.parse(expr)
            a = m.body[0]  # 如果json非常不规则，这一步会有异常
        except Exception as e:
            raise ParserException(29, str(e))

        def parse(node):
            if isinstance(node, ast.Expr):
                return parse(node.value)
            elif isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.Str):
                return node.s
            elif isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Dict):
                return dict(zip(map(parse, node.keys), map(parse, node.values)))
            elif isinstance(node, ast.List):
                return map(parse, node.elts)
            else:
                raise NotImplementedError(node.__class__)

        return parse(a)

    @classmethod
    def remove_html_tags(cls, html_src, quick=False):
        """移除html-doc的html-tags
        :param html_src:原始html文本
        :param quick:
                    True：使用re替换（有小Bug：匹配不完备）
                    False：使用lxml的html parser（相对较完备，相对速度较慢）
        :return: 移除html-tags后的文本
        """
        if quick:
            result = re.sub(r'</?\w+[^>]*>', '', html_src, flags=re.S)
        else:
            parser = LXML_HTMLParser()
            try:
                html = '<div>{}</div>'.format(html_src)
                result = ''.join(etree_from_string(html, parser).itertext())
            except Exception:  # TO FIX
                result = html_src
        return result


def extract_index_json(text):
    json_p = re.compile('window.pageData =(.*?)</script>', re.S)
    js_data_list = json_p.findall(text)
    if not js_data_list:
        raise Exception
    js_data_ori = js_data_list[0]
    js_data_ori = js_data_ori[:js_data_ori.rindex('}') + 1].strip()
    js_data = Utils.parse_js(js_data_ori)

    # json_p = re.findall(r'window.pageData = (\{.+?\})\;', text, re.S)[0]
    # json_data = json.loads(dict_data)
    return js_data
