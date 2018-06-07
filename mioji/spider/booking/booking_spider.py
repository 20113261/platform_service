#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年3月28日

@author: chenjinhui
'''
import datetime
import json
import re
import sys
from lxml import html as HTML
from mioji.common.logger import logger
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from bookingutils import check_is_breakfast_free
from mioji.common.class_common import Room
from mioji.common.task_info import Task
from mioji.common import parser_except
import traceback
reload(sys)
sys.setdefaultencoding('utf-8')

home_url = 'http://www.booking.com'
crawl_url = 'http://www.booking.com/%s.zh-cn.html?checkin=%s;checkout=%s;selected_currency=CNY;%s'

class BookingSpider(Spider):
    
    # 抓取目标 如城市列表、酒店列表 等对象
    source_type = 'bookingHotel'
    
    # 数据目标 如城市、酒店数据、酒店房型数据等。
    #   一个抓取目标可以对应多个，数据对象。
    #   一个抓取数据对应一个解析方法 parse_xxx 如：parse_hotelList_hotel，parse_hotelList_room
    targets = {
        'room': {'version': 'InsertHotel_room3'}
        }
    
    # 对应多个老原爬虫
    old_spider_tag = {
        # 例行sectionname
        'bookingHotel':{'required':['room']}
        }
    
    # unable = True

    def __init__(self, task=None):
        super(BookingSpider, self).__init__(task)
        self.cid = None
        self.para_list = None
        self.headers = {}
        self.hotel_id = None
        self.tax_alist = []
        self.tax_list = ['税费', '城市税', '住宿方服务费', '度假村费', '目的地附加费', '增值税']
        self.tax_cent = 0
        self.tax_other = ''

        if task:
            self.task = task
            self.process_task_info()

    def targets_request(self):
        '''
        1. 如果有多个请求，每个结果都会回调数据解析函数，可以通过req判断是否需要解析。
        2. 同时如果有多个 目标数据 那么每个请求结果 也都会回调多个解析方法
            但可以通过 crawl(required=['target'])，来指定任务需要的数据目标,避免不必要资源浪费
        3. 每个请求可以通过 user_handler 来指定请求数据回调 （用于流程的参数解析。指定了必然会回调）
        4. 每个请求加上注释 @request(retry_count=3, proxy_type=PROXY_FLLOW, async=True)
            binding 绑定解析方法
        5. 一个请求可以一组同类型请求，如pages且如果可以同步进行那么注释加上async=True即可。
            参考booking hotels_list_spider    
        6. 一类的请求如果存在多个，但必须一个完成后才能知道下一个请求。那么可以用yield实现。
            参考hotels hotels_list_spider
        7. 所有的数据回调接口，user_handler,cache_check,parse_xx 都必须是两个参数（req,data）且data是转换后的数据类型。
        8. 如果分发多个请求，可以再请求json中加入自己需要的数据(不要使用框架的key,@伟松 抓取源城市列表实践发现)
        '''

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def base_request():
           return {
               'req': {'url': home_url},
                'data': {'content_type': 'html'},
           }

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=[self.parse_room])
        def next_request():
            self.headers['Host'] = 'www.booking.com'
            url = crawl_url % (str(self.para_list['url_hotel_name']), str(self.para_list['check_in']), str(self.para_list['check_out']), str(self.para_list['info']))
            self.headers['Referer'] = url
            return {'req': {'url': url, 'headers': self.headers},
                    'data': {'content_type': 'html'}}

        return [base_request, next_request]

    def get_age_info(self, age):
        # it's child when age < 18, otherwise it's adult
        r = age.split('|')
        no_adult = 0
        no_child_l = []
        no_child = 0
        for e in r:
            age_l = e.split('_')
            for m in age_l:
                if int(m) < 18:
                    no_child += 1
                    no_child_l.append('req_age=' + m)
                else:
                    no_adult += 1
        res = {}
        res['no_adult'] = str(no_adult)
        res['no_child'] = str(no_child)
        res['age_child'] = no_child_l
        return res

    def tax_parse(self, tax_l):
        self.tax_cent = 0
        self.tax_other = ''
        if len(tax_l) > 1:
            for i in self.tax_list:
                if i in tax_l[1]:
                    i = u'{0}'.format(i)
                    pipl = re.compile('[\d\.]+\%'u'{0}'.format(i))
                    pipr = re.compile('[\d\.]+\%')
                    if pipl.findall(tax_l[1]) == []:
                        if '、' in tax_l[1]:
                            li = tax_l[1].split('、')
                        else:
                            li = tax_l[1].split(',')
                        for x in li:
                            if i in x:
                                self.tax_other += '不包含' + x + '；'
                                self.tax_other = self.tax_other.replace(':', '')
                        tax_cent = ['0']
                    else:
                        tax_cent = pipr.findall(pipl.findall(tax_l[1])[0])
                    if tax_cent != []:
                        self.tax_cent += float(tax_cent[0].replace('%', ''))
                    else:
                        if '、' in tax_l[1]:
                            li = tax_l[1].split('、')
                        else:
                            li = tax_l[1].split(',')
                        for x in li:
                            if i in x:
                                self.tax_other += '不包含' + x + '；'
        elif tax_l == '':
            self.tax_cent = 0
            self.tax_other = ''
        else:
            self.tax_cent = 0
            if '房价包括' in tax_l[0]:
                self.tax_other += '房价包括' + tax_l[0].split('房价包括')[1].replace('_','')
            else:
                self.tax_other += tax_l[0].replace('\n', '')
        print self.tax_cent, self.tax_other
        return self.tax_cent, self.tax_other

    def get_info(self, info_l):
        no_room = info_l[0]
        no_man = info_l[1]
        age = info_l[2]
        age_info = self.get_age_info(age)
        # print age_info
        res = 'req_adults=' + age_info['no_adult'] + ';' + ';'.join(age_info['age_child']) + ';req_children=' + age_info[
            'no_child']

        return res
    
    def parse_tr(self, tr, add_flag, other_price_desc, room_type, check_in_time, check_out_time, tax_cent, tax_other):
        # occupancy  occupancy
        # 初始值，防止因找不到报错
        other_info = {}
        occupancy = -1
        rest = -1
        occu = ''
        return_rule = change_rule ="NULL"
        source_roomid = ''
        is_breakfast_free = is_cancel_free = has_breakfast = "NULL"
        pay_method = ''
        related_clauses_detail = []
        price = float(-1.0)
        try:
            occu = tr.xpath('./td[' +str(int(1+add_flag))+']/*//span[@class="invisible_spoken"]/text()')[0]
            oc = re.findall(r" (\d+?)", occu)
            if oc:
                occupancy = 0
                for o in oc:
                    occupancy += int(o)
            else:
                occupancy = -1
        except Exception, e:
            occupancy = -1
        try:
            price_desc = tr.xpath('./td[' +str(int(2+add_flag))+']/div/strong/text()')[0]
            price = price_desc[:-2].replace('\n', '').strip().replace(',', '')
            if tax_cent == '':
                if tr.xpath('./td[' + str(int(2 + add_flag)) + ']/div')[1].text_content() != '':
                    tax_a = tr.xpath('./td[' + str(int(2 + add_flag)) + ']/div')[1].text_content().replace(' ', '').split('\n')
                elif tr.xpath('./td[' + str(int(2 + add_flag)) + ']/div')[2].text_content() != '':
                    tax_a = tr.xpath('./td[' + str(int(2 + add_flag)) + ']/div')[2].text_content().replace(' ', '').split('\n')
                elif tr.xpath('./td[' + str(int(2 + add_flag)) + ']/div')[3].text_content() != '':
                    tax_a = tr.xpath('./td[' + str(int(2 + add_flag)) + ']/div')[3].text_content().replace(' ', '').split('\n')
                tax_a = '_'.join([a for a in tax_a if a is not u''])
                self.tax_alist = tax_a.split('不包含')
                tax_cent, tax_other = self.tax_parse(self.tax_alist)
                price = float(price) * (1 + tax_cent/100)
            else:
                price = float(price) * (1 + tax_cent/100)
                tax_other = tax_other
        except Exception, e:
            price_desc = ''
            pass

        other_info['price_desc'] = other_price_desc.encode('utf-8')
        try:
            room_id = tr.xpath('./td[' +str(int(2+add_flag))+']/div/@id')[0][8:]
            source_roomid = room_id.encode('utf-8')
        except Exception, e:
            room_id = 'NULL'
            pass
        related_clauses = ''
        try:
            spans_desc = tr.xpath(
                './td[' +str(int(3+add_flag))+']/*//li[contains(@class, "hp-rt__policy__item")]/span/text()|./td[' +str(int(3+add_flag))+']/*//li[contains(@class, "hp-rt__policy__item")]/span/*/text()')
            related_clauses = '||'.join(
                [spa.replace('\n', '').strip().encode('utf-8') for spa in spans_desc if spa != '\n' and len(spa.strip())])
        except:
            pass
        other_info['related_clauses'] = related_clauses
        max_select_count = -1
        try:
            max_select_count = tr.xpath("./*//select/@data-rc")[0].strip()
            max_select_count = int(max_select_count)
        except:
            pass

        other_info['max_select_count'] = max_select_count
        try:
            # 分三个部分，第一部分是早餐，第二部分是退订相关，第三是预付款项
            re_ru_list = tr.xpath('./td[' +str(int(3+add_flag))+']/*//div[contains(@class, "differing_policies")]/p')
            related_clauses_detail = []

            check_part_count = 0
            food_res = ''
            rutu_res = ''
            for re_ru in re_ru_list:
                ##print re_ru
                pc_info = re_ru.xpath("./*/text()")
                p_info = re_ru.xpath("./text()")
                # print p_info
                pc_desc = ' '.join(
                    [pc.replace('\n', '').strip() for pc in pc_info if pc != '\n' and len(pc.strip())])
                p_desc = ' '.join([p.replace('\n', '').strip() for p in p_info if p != '\n' and len(p.strip())])

                rules_result = self.parse_room_rules(re_ru)

                if rules_result[0] == 0:
                    # 三餐
                    check_part_count += 1
                    has_breakfast = 'Yes' if rules_result[2] else 'No'
                    is_breakfast_free = 'Yes' if rules_result[3] else 'No'
                    food_res = rules_result[1]


                elif rules_result[0] == 1:
                    # 退改
                    check_part_count += 1

                    return_rule_info = rules_result[1]

                    # 退改条款一样
                    return_rule = return_rule_info
                    change_rule = return_rule_info
                    is_cancel_free = 'Yes' if rules_result[2] else 'No'
                    if is_cancel_free == 'Yes' and ('免费取消期限' in rules_result[1] or '如果取消订单' in rules_result[1]):
                        is_cancel_free = 'NULL'
                    rutu_res = rules_result[1]

                elif rules_result[0] == 2:
                    # 预付款
                    check_part_count += 1
                    pay_method = rules_result[1]

            if check_part_count != 3:
                # logger.warn('早餐、退订、预付款 信息缺失')
                pass
        except Exception, e:
            pass
        other_info['related_clauses_detail'] = '||'.join(related_clauses_detail).encode('utf-8')
        # print return_rule
        other_info['check_in_time'] = check_in_time
        other_info['check_out_time'] = check_out_time
        # rest #rest 剩余房间
        # 同max_select_count by 佐俊 @201609014
        try:
            rest_info = tr.xpath("./*//select/@data-rc")[0]
            rest = int(rest_info)
        except Exception, e:
            pass
        # rest = rest
        return (occupancy,price,source_roomid,related_clauses,
                has_breakfast, is_breakfast_free, return_rule,
                change_rule,is_cancel_free, pay_method, rest, other_info,
                tax_other, occu, food_res,rutu_res)

    def parse_room_rules(self, rules_node):
        '''
        @param rules_node:
        @return: ()
            [0]type,     0 三餐；1 退改；2 预付款项
            [1]rule_des, 条款内容
            ...
            type=0
                [2]是否含早
                [3]早餐是否免费
            type=1
                [2]是否免费退改
        '''
        pc_info = rules_node.xpath("./*/text()")
        p_info = rules_node.xpath("./text()")
        # print p_info
        pc_desc = ' '.join([pc.replace('\n', '').strip() for pc in pc_info if pc != '\n' and len(pc.strip())])
        p_desc = ' '.join([p.replace('\n', '').strip() for p in p_info if p != '\n' and len(p.strip())])
        des = pc_desc + " " + p_desc
        des = des.encode('utf-8')

        # 早餐
        if '餐' in des:
            if '餐需另付' in des:
                has_breakfast = False
                is_breakfast_free = False
            else:
                has_breakfast = u'早餐' in des
                is_breakfast_free = False

                if has_breakfast:
                    if check_is_breakfast_free(des):
                        is_breakfast_free = 'Yes'
                    else:
                        is_breakfast_free = 'No'

            return 0, des, has_breakfast, is_breakfast_free

            # 退改
        p_id = rules_node.xpath('@id')
        if len(p_id) == 1 and p_id[0] == 'cancel_policy_first':
            is_cancel_free = u'不收取费用' in des or u'免费取消' in des
            return 1, des, is_cancel_free

            # 预付
        return 2, des
    
    def cache_check(self, req, data):
        '''
        该回调可用于检测缓存是否有效\正确。
        :return: False 框架会重新走数据请求
        '''
        return Spider.cache_check(self, req, data)
    
    def parse_room(self, req, data):
        # 可以通过request binding=[]指定解析方法
        check_out = self.para_list['check_out'].encode('utf-8')
        check_in = self.para_list['check_in'].encode('utf-8')
        hotel_id = self.hotel_id
        cid = self.cid
        room_infos = self.parseRoom(data, check_in, check_out,
                                 hotel_id, cid)
        return room_infos

    def process_task_info(self):
        self.cid = self.task.ticket_info.get('cid', None)
        taskcontent = self.task.content
        # if task.ticket_info.has_key('occ'):
        #     global global_occ
        #     glocal_occ = task.ticket_info['occ']
        task = self.task
        try:
            taskcontent = taskcontent.strip()
            info_list = taskcontent.split('&')
            hotel_id, url_hotel_name, nights, check_in_temp = info_list[0], \
                                                            info_list[1], info_list[2], info_list[3]

            check_in = check_in_temp[:4] + '-' + check_in_temp[4:6] + '-' + check_in_temp[6:]
            check_out_temp = datetime.datetime(int(check_in_temp[:4]), int(check_in_temp[4:6]), int(check_in_temp[6:]))
            check_out = str(check_out_temp + datetime.timedelta(days=int(nights)))[:10]
            peoples = task.ticket_info['room_info'][0].get('occ', 2)
            room_num = task.ticket_info['room_info'][0].get('num', 1)
            info = 'req_adults=' + str(peoples) + ';no_rooms=' + str(room_num)
            if len(info_list) > 4:
                info = self.get_info(info_list[4:])
        except Exception, e:
            raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                'Content Error:{0}'.format(self.task.content))
        self.para_list = {'url_hotel_name': url_hotel_name,
                            'check_in': check_in,
                            'check_out': check_out,
                            'info': info}
        self.hotel_id = hotel_id

    def parseRoom(self, content, check_in, check_out, hotel_id, cid):
        room_infos = []
        tree = content
        try:
            hotel_name = tree.xpath('//*[@id="hp_hotel_name"]/text()')[0].strip().encode('utf-8')
        except Exception as e:
            print 'error in line 350 meg is {0}'.format(e)
            raise parser_except.ParserException(parser_except.PROXY_INVALID, 'bookingHotel::代理异常')

        print 'hotel_name=>%s' % hotel_name
        content = HTML.tostring(content)
        try:
            city = re.findall(r"city_name: '(.*?)',", content)[0]
            # city = tree.xpath('//span[@class="hp_address_subtitle jq_tooltip"]/text()')[0].split(',')[-2].split(' ')[-1]
        except:
            city = 'NULL'

        print 'city=>%s' % city
        # pay_method
        try:
            pay_list = tree.xpath('//p[contains(@class,"payment_methods")]/button/@aria-label')
            pay_card = '||'.join(pay_list)
            pay_card = pay_card.encode('utf-8')

        except:
            pay_card = ''
        print 'pay_card=>%s' % pay_card
        try:
            extrabed_rules = tree.xpath("//div[contains(@class, 'description_children-policy')]/*//text()")
            extrabed_rule = ' '.join([ex.strip() for ex in extrabed_rules if ex != '\n'])
            extrabed_rule = extrabed_rule.encode('utf-8')
            # print extrabed_rule
        except:
            extrabed_rule = ''
        # is_extrabed  is_extrabed_free
        print 'extrabed_rule=>%s' % extrabed_rule
        try:
            if u'加床收费' in extrabed_rule or u'一间客房增加' in extrabed_rule or u'加床的收费' in extrabed_rule:
                is_extrabed = 'Yes'
            else:
                is_extrabed = ''
        except:
            pass
        print 'is_extrabed=>%s' % is_extrabed
        try:
            if u'免费加床' in extrabed_rule or u'加床免费' in extrabed_rule:
                is_extrabed_free = 'Yes'
            else:
                is_extrabed_free = ''
        except:
            pass
            # check_in_time
        print 'is_extrabed_free=>%s' % is_extrabed_free
        check_in_time = ''
        try:
            check_in_time = tree.xpath('//span[@data-component="prc/timebar"]/@data-from-label')[-1].replace('\n', '').strip().encode(
                'utf-8')
            # print check_in_time
        except Exception, e:
            pass
        print 'check_in_time=>%s' % check_in_time
        # check_out_time
        check_out_time = ''
        try:
            check_out_time = tree.xpath('//span[@data-component="prc/timebar"]/@data-until-label')[-1].replace('\n', '').strip().encode(
                'utf-8')
            # print check_out_time
        except Exception, e:
            pass
        print 'check_out_time=>%s' % check_out_time
        # review_num
        try:
            review_num = re.findall('(\d+)', tree.xpath('//*[@id="show_reviews_tab"]/span')[0].text_content().replace(',','').strip())[0]
        except:
            review_num = '0'
        print 'review_num =>%s' % review_num
        # img_list
        img_list = []
        try:
            for a in tree.xpath('//*[@id="photos_distinct"]/a'):
                try:
                    href = a.attrib['href']
                    if '.jpg' in href:
                        img_list.append(href)
                except:
                    pass
        except:
            pass

        img_list = '|'.join(img_list)
        print 'img_list=>%s' % img_list
        tr_list = tree.xpath('//tr[contains(@class, "room_loop_counter")]')
        #print len(tr_list), tr_list
        # 获取maintr
        maintr_list = tree.xpath('//tr[contains(@class, "maintr")]')
        #print len(maintr_list)
        # 获取extendedRow
        extr_list = tree.xpath('//tr[contains(@class, "extendedRow")]')
        #print len(extr_list)
        # 设置计时器
        maintr_flag = extr_flag = 0
        main_max_length = len(maintr_list)

        content = HTML.fromstring(content)
        if not tr_list:
            room_infos = self.new_parse_room(content,check_in,check_out,hotel_id,cid)
            return room_infos
        try:
            tax_cent = ''
            tax_other = ''
            for tr in tr_list:
                other_price_desc = ''
                if tr.xpath(".//div[@class='incExcInPriceNew']") != []:
                    self.tax_alist = tr.xpath(".//div[@class='incExcInPriceNew']")[0].text_content().replace('\n','').split('不包含')
                    tax_cent, tax_other = self.tax_parse(self.tax_alist)
                if maintr_flag < main_max_length and tr == maintr_list[maintr_flag]:
                    room_type = ''
                    try:
                        room_type_info = tr.xpath('./td//a[contains(@class, "jqrt")]//text()')#[0].encode('utf-8')
                        print "room_type_info", room_type_info
                        for ri in room_type_info:
                            if len(ri.replace('\n', '')):
                                room_type = ri
                                break
                        room_type = room_type.replace('\n', '').encode('utf-8')
                    except Exception, e:
                        pass

                    try:
                        bed_types = tr.xpath('./td[1]/*//li[@class="rt-bed-type"]//text()')
                        if len(bed_types) == 0:
                            bed_types = tr.xpath('./td[1]/*//li[@class="bedroom_bed_type"]//text()')
                        if len(bed_types) == 0:
                            bed_types = []
                        bed_type = '||'.join(be.strip() for be in bed_types if be != '\n' and len(be.strip()))
                        bed_type = bed_type.replace(u"||和||", u'和')
                        bed_type = bed_type.encode('utf-8')
                    except Exception, e:
                        bed_type = 'NULL'
                        # print 'bed type error'
                        pass

                        # room_desc
                    room_desc = ''
                    try:
                        # 房间设施
                        # <span class="highlighted_facilities_reinforcement" >
                        facs_node_text_list = tr.xpath(
                            './td/*//span[contains(@class, "highlighted_facilities_reinforcement")]//span/text()')
                        # 过滤字符 •
                        facs = [fa.replace(u'\u2022', '').strip() for fa in facs_node_text_list if
                                fa != '\n' and len(fa.strip())]
                        fac_lists = list(set(facs))
                        room_desc = ';'.join(map(lambda x: x.strip().encode('utf-8'), fac_lists))
                    except:
                        # print 'room_desc error'
                        pass
                        # size
                    size = -1
                    try:
                        # <span class="jq_tooltip hp_rt_rs_ds">33 平方米<
                        fac_lists = tr.xpath("./td[1]/span/*//span/text()")
                        size_node_text = tr.xpath('./td/*//span[contains(@class, "jq_tooltip hp_rt_rs_ds")]/text()')[0].encode(
                            'utf-8')
                        try:
                            # size = re.findall(u'\d*', size_node_text)[0]
                            # self.local_debug_log('re find %s' % size)
                            size = int(size_node_text.replace(u'平方米', '').strip())
                        except Exception, e:
                            size = -1
                            pass
                    except Exception, e:
                        pass
                    # price_rela_info

                    other_price_desc = ''
                    try:
                        div_list = tr.xpath("./td[1]/*//div[contains(@class, 'incExcInPriceNew')]")
                        room_price_desc = []
                        # print len(div_list)
                        for div in div_list:
                            temp = ''
                            span_desc = []
                            try:
                                span_desc = div.xpath("./span/text()")[0].strip().encode('utf-8')
                            except:
                                pass
                                # print str(span_desc)
                            div_info = []
                            try:
                                div_info = div.xpath("./text()")
                            except:
                                pass
                                # print div.xpath("./text()")
                            div_desc = ' '.join([dp.replace('\n', '').strip().encode('utf-8') for dp in div_info if
                                                dp != '\n' and len(dp.strip())])
                            div_list = div_desc.split(':')

                            div_list.insert(1, span_desc)
                            # print div_list
                            # print 12
                            temp = " ".join([di.replace('\n', '').strip().encode('utf-8') for di in div_list if
                                            di != '\n' and len(di.strip())])
                            # print temp, 'p'
                            # temp = ' '.join((span_desc,div_desc))
                            room_price_desc.append(temp)
                            # other_price = tr.xpath("./td[1]/div[4]/div/text()")
                        other_price_desc = ';'.join([op.strip() for op in room_price_desc if op != '\n' and len(op.strip())])
                        # 第二种网页结构是在maintr里面
                        try:
                            tu = self.parse_tr(tr, 1, other_price_desc, room_type, check_in_time, check_out_time, tax_cent, tax_other)
                            occupancy,price,source_roomid,related_clauses,has_breakfast, is_breakfast_free, return_rule,change_rule, \
                            is_cancel_free, pay_method, rest, other_info, tax_other, occu, food_res, rutu_res= tu
                            if price == float(-1.0):
                                raise  Exception("该网页结构不是第二种，房间没有解析到价格")
                            # print tu
                            # room
                            room = Room()
                            room.currency = 'CNY'
                            room.source = 'booking'
                            room.real_source = 'booking'
                            room.hotel_name = hotel_name
                            room.city = cid
                            room.check_in = check_in
                            room.check_out = check_out
                            room.source_hotelid = hotel_id

                            print '>>>>>>>>>>>>>>>>>>>>>>>>>>'
                            if len(room_type):
                                room.room_type = room_type
                            if len(bed_type):
                                room.bed_type = bed_type
                            if len(room_desc):
                                room.room_desc = room_desc
                            if tax_other in room_desc:
                                room.room_desc = room_desc
                            else:
                                room.room_desc = room_desc + tax_other
                            other_info = other_info
                            if len(pay_card):
                                other_info['pay_card'] = pay_card

                            other_info['review_nums'] = review_num
                            other_info['img_urls'] = img_list

                            if len(extrabed_rule):
                                room.extrabed_rule = extrabed_rule
                                # print 23
                            if len(is_extrabed):
                                room.is_extrabed = is_extrabed

                            if len(is_extrabed_free):
                                room.is_extrabed_free = is_extrabed_free
                                # size
                            try:
                                room.size = int(size)
                            except:
                                pass
                            # occupancy
                            try:
                                room.occupancy = occupancy
                            except Exception, e:
                                pass
                                # print e
                                # print 'occupaccy error'

                                # price
                            try:
                                room.price = float(price)
                                if room.price < .0:
                                    continue
                                # print price
                            except Exception, e:
                                # print 'price error'
                                # print e
                                pass

                            # room_id source_roomid

                            try:
                                room.source_roomid = source_roomid.encode('utf-8')
                            except Exception, e:
                                pass

                            # return_rule change_rule has_breakfast is_breakfast_free is_cancel_free
                            try:
                                # 分三个部分，第一部分是早餐，第二部分是退订相关，第三是预付款
                                room.has_breakfast = has_breakfast
                                room.is_breakfast_free = is_breakfast_free

                                # 退改条款一样
                                room.return_rule = return_rule
                                room.change_rule = change_rule
                                room.is_cancel_free = is_cancel_free
                                room.pay_method = pay_method
                            except Exception as e:
                                pass
                            # other_info
                            other_info['extra'] = {'breakfast':food_res,
                                                   'payment':pay_method,
                                                   'return_rule':rutu_res,
                                                   'occ_des':occu.replace('\n','')}
                            room.other_infos = json.dumps(other_info, ensure_ascii=False).encode('utf-8')
                            try:
                                room.rest = rest
                            except Exception, e:
                                pass
                            # -- end rest

                            if '支付方式以原网站为准' in room.pay_method:
                                room.pay_method = '支付方式'
                            elif '需要预付' in room.pay_method and '晚房费' in room.pay_method:
                                room.pay_method = '支付方式'
                            elif '无需预付' in room.pay_method:
                                room.pay_method = '到店支付'
                            elif '需预付' in room.pay_method and '全额' in room.pay_method:
                                room.pay_method = '在线支付'

                            room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid, \
                                        room.real_source, room.room_type, room.occupancy, room.bed_type, room.size, room.floor, \
                                        room.check_in, room.check_out, room.rest, room.price, room.tax, room.currency, room.pay_method, \
                                        room.is_extrabed, room.is_extrabed_free, room.has_breakfast, room.is_breakfast_free, \
                                        room.is_cancel_free, room.extrabed_rule, room.return_rule, room.change_rule, room.room_desc, \
                                        room.other_infos, room.guest_info)
                            room_infos.append(room_tuple)
                        except Exception as e:
                            print traceback.format_exc()
                    except Exception, e:
                        print e
                        pass
                        # print e
                    maintr_flag += 1
                    continue
                elif extr_flag < main_max_length and tr == extr_list[extr_flag]:
                    # 分隔
                    extr_flag += 1
                    continue
                else:

                    try:
                        tu = self.parse_tr(tr, 0, other_price_desc, room_type, check_in_time, check_out_time, tax_cent, tax_other)
                        occupancy,price,source_roomid,related_clauses,has_breakfast, \
                        is_breakfast_free, return_rule,change_rule,\
                        is_cancel_free, pay_method, rest, other_info ,tax_other,occu,food_res,rutu_res= tu
                        if price == float(-1.0):
                            raise  Exception("该网页结构不是第一种，房间没有解析到价格")
                        # print tu
                        # room
                        room = Room()
                        room.currency = 'CNY'
                        room.source = 'booking'
                        room.real_source = 'booking'
                        room.hotel_name = hotel_name
                        room.city = cid
                        room.check_in = check_in
                        room.check_out = check_out
                        room.source_hotelid = hotel_id

                        if len(room_type):
                            room.room_type = room_type
                        if len(bed_type):
                            room.bed_type = bed_type
                        if len(room_desc):
                            room.room_desc = room_desc
                        if tax_other in room_desc:
                            room.room_desc = room_desc
                        else:
                            room.room_desc = room_desc + tax_other
                        other_info = other_info
                        if len(pay_card):
                            other_info['pay_card'] = pay_card

                        other_info['review_nums'] = review_num
                        other_info['img_urls'] = img_list

                        if len(extrabed_rule):
                            room.extrabed_rule = extrabed_rule
                            # print 23
                        if len(is_extrabed):
                            room.is_extrabed = is_extrabed

                        if len(is_extrabed_free):
                            room.is_extrabed_free = is_extrabed_free
                            # size
                        try:
                            room.size = int(size)
                        except:
                            pass
                        # occupancy
                        try:
                            room.occupancy = occupancy
                        except Exception, e:
                            pass
                            # print e
                            # print 'occupaccy error'

                            # price
                        try:
                            room.price = float(price)
                        except Exception, e:
                            # print 'price error'
                            # print e
                            pass

                        # room_id source_roomid
                        try:
                            room.source_roomid = source_roomid.encode('utf-8')
                        except Exception, e:
                            pass

                        # return_rule change_rule has_breakfast is_breakfast_free is_cancel_free
                        try:
                            # 分三个部分，第一部分是早餐，第二部分是退订相关，第三是预付款
                            room.has_breakfast = has_breakfast
                            room.is_breakfast_free = is_breakfast_free

                            # 退改条款一样
                            room.return_rule = return_rule
                            room.change_rule = change_rule
                            room.is_cancel_free = is_cancel_free
                            room.pay_method = pay_method
                        except Exception as e:
                                pass
                        # other_info
                        other_info['extra'] = {
                            'breakfast': food_res,
                            'payment': pay_method,
                            'return_rule': rutu_res,
                            'occ_des': occu.replace('\n','')
                        }
                        room.other_infos = json.dumps(other_info, ensure_ascii=False).encode('utf-8')

                        if '支付方式以原网站为准' in room.pay_method:
                            room.pay_method = '支付方式'
                        elif '需要预付' in room.pay_method and '晚房费' in room.pay_method:
                            room.pay_method = '支付方式'
                        elif '无需预付' in room.pay_method:
                            room.pay_method = '到店支付'
                        elif '需预付' in room.pay_method and '全额' in room.pay_method:
                            room.pay_method = '在线支付'

                        try:
                            room.rest = rest
                        except Exception, e:
                            pass
                        # -- end rest
                        room.city = cid
                        print room.city
                        room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid, \
                                    room.real_source, room.room_type, room.occupancy, room.bed_type, room.size, room.floor, \
                                    room.check_in, room.check_out, room.rest, room.price, room.tax, room.currency, room.pay_method, \
                                    room.is_extrabed, room.is_extrabed_free, room.has_breakfast, room.is_breakfast_free, \
                                    room.is_cancel_free, room.extrabed_rule, room.return_rule, room.change_rule, room.room_desc, \
                                    room.other_infos, room.guest_info)
                        room_infos.append(room_tuple)
                    except Exception as e:
                        raise Exception(str(e))
        except:
            print traceback.format_exc()
        return room_infos

    def new_parse_room(self, content, check_in, check_out, hotel_id, cid):
        print "进入新的解析"
        room_infos = []
        tree = content
        try:
            hotel_name = tree.xpath('//*[@id="hp_hotel_name"]/text()')[0].strip().encode('utf-8')
        except Exception as e:
            print 'error in line 350 meg is {0}'.format(e)
            raise parser_except.ParserException(parser_except.PROXY_INVALID, 'bookingHotel::代理异常')
        print 'hotel_name=>%s' % hotel_name
        content = HTML.tostring(content)
        try:
            city = re.findall(r"city_name: '(.*?)',", content)[0]
        except:
            city = 'NULL'
        print 'city=>%s' % city

        try:
            pay_list = tree.xpath("//p[contains(@class, 'payment_methods')]/button/@aria-label")
            pay_card = '||'.join(pay_list)
            pay_card = pay_card.encode('utf-8')
        except:
            pay_card = ''
        print "pay_card:", pay_card

        try:
            extrabed_rules = tree.xpath("//div[contains(@class, 'description_children-policy')]/*//text()")
            extrabed_rule = ' '.join([ex.strip() for ex in extrabed_rules if ex != '\n'])
            extrabed_rule = extrabed_rule.encode('utf-8')
        except:
            extrabed_rule = 'NULL'
        print 'extrabed_rule=>%s' % extrabed_rule

        try:
            if u'加床收费' in extrabed_rule or u'一间客房增加' in extrabed_rule or u'加床的收费' in extrabed_rule:
                is_extrabed = 'Yes'
            else:
                is_extrabed = ''
        except:
            pass
        print 'is_extrabed=>%s' % is_extrabed

        try:
            if u'免费加床' in extrabed_rule or u'加床免费' in extrabed_rule:
                is_extrabed_free = 'Yes'
            else:
                is_extrabed_free = ''
        except:
            pass
        print 'is_extrabed_free=>%s' % is_extrabed_free
        check_in_time = ''
        try:
            check_in_time = tree.xpath("//span[@data-component='prc/timebar']/@data-from-label")[-1].replace('\n',
                                                                                                             '').strip().encode(
                'utf-8')
        except Exception, e:
            pass
        print 'check_in_time=>%s' % check_in_time
        check_out_time = ''
        try:
            check_out_time = tree.xpath("//span[@data-component='prc/timebar']/@data-until-label")[-1].replace('\n',
                                                                                                               '').strip().encode(
                'utf-8')
        except Exception, e:
            pass
        print 'check_out_time=>%s' % check_out_time

        try:
            review_num = re.findall('(\d+)',
                                    tree.xpath('//*[@id="show_reviews_tab"]/span')[0].text_content().replace(',',
                                                                                                             '').strip())[
                0]
        except:
            review_num = '0'
        print 'review_num =>%s' % review_num

        img_list = []
        try:
            for a in tree.xpath('//*[@id="photos_distinct"]/a')[:20]:
                try:
                    href = a.attrib['href']
                    if '.jpg' in href:
                        img_list.append(href)
                except:
                    pass
        except:
            pass
        img_list = '|'.join(img_list)
        print 'img_list=>%s' % img_list

        tr_list = tree.xpath('//form[@id="hprt-form"]/table/tbody/tr')
        tr_list = [tr for tr in tr_list if tr.attrib.get('data-block-id', None)]
        if not tr_list:
            room_infos = self.new_parse_three_room(tree, check_in, check_out, hotel_id, cid)
            return room_infos
        tax_cent = ''
        tax_other = ''
        for tr in tr_list:
            if tr.xpath('./@class') == 'hprt-cheapest-block-row':
                continue
            if tr.xpath("./td//div[@class='hptr-taxinfo-block']") != []:
                self.tax_alist = tr.xpath("./td//div[@class='hptr-taxinfo-block']")[0].text_content().replace('\n','').split('不包含')
                tax_cent, tax_other = self.tax_parse(self.tax_alist)
            room_type = ""
            try:
                if tr.xpath('./td[contains(@class,"roomtype")]//a[@class="hprt-roomtype-link"]') != []:
                    room_type = tr.xpath('./td[contains(@class,"roomtype")]//a[@class="hprt-roomtype-link"]')[0].text_content()
                    room_type = room_type.replace('\n', '').encode('utf-8')
                elif tr.xpath(".//a[@class='hprt-roomtype-link hp-rt-room-name-wrapper']") != []:
                    room_type = tr.xpath(".//a[@class='hprt-roomtype-link hp-rt-room-name-wrapper']")[0].text_content().replace('\n','')
                else:
                    pass
            except Exception as e:
                pass
            print "room_type:", room_type
            bed_types = ""
            try:
                bed_types = tr.xpath('./td[contains(@class,"roomtype")]//li[@class="rt-bed-type"]')[0].text_content()
                bed_type = bed_types.replace('\n', '').encode('utf-8')
            except Exception as e:
                bed_type = 'NULL'
                pass
            print "bed_type:", bed_type

            try:
                rest_desc = tr.xpath('')
            except:
                pass
            room_desc = ""
            try:
                # 房间设施
                div_span = tr.xpath(
                    './td[contains(@class,"roomtype")]//span[contains(@class,"hprt-facilities")]/span/text()')
                li_span = tr.xpath(
                    './td[contains(@class,"roomtype")]//div/ul[contains(@class,"hprt-facilities")]//span/text()')
                li_span = [li.replace(u'\u2022', '').strip() for li in li_span]
                div_span.extend(li_span)
                room_desc = ';'.join(map(lambda x: x.strip().encode('utf-8'), div_span))
            except Exception as e:
                pass
            print "room_desc:", room_desc

            size = -1
            try:
                size_desc = tr.xpath(
                    './td[contains(@class,"roomtype")]//div[@class="hprt-facilities-block"]/span[@class="hprt-facilities-facility"]/span')[
                    0].text_content()
                size = re.search(u'[0-9]+', size_desc).group()
            except Exception as e:
                size = -1

            print "size:", size
            other_price_desc = ""
            try:
                span_list = tr.xpath(
                    './td[contains(@class,"roomtype")]//div[@class="hprt-roomtype-block"]//div[@class="hptr-taxinfo-details"]/span/text()')
                div_list = tr.xpath(
                    './td[contains(@class,"roomtype")]//div[@class="hprt-roomtype-block"]//div[@class="hptr-taxinfo-details"]/text()')
                div_list = [div.replace('\n', '') for div in div_list if div != '\n']
                temp_price_desc = [''.join([span.strip(':'), div]) for span, div in zip(span_list, div_list)]
                other_price_desc = ';'.join(temp_price_desc[::-2])
            except Exception as e:
                pass

            other_info = {}
            rest = -1
            return_rule = change_rule = 'NULL'
            is_breakfast_free = is_cancel_free = has_breakfast = "NULL"
            pay_method = ''
            related_clauses_detail = []
            price = float(-1.0)

            try:
                occu = tr.xpath(
                    './td[contains(@class,"occupancy")]//div[contains(@class,"hprt-occupancy-occupancy")]/@data-title')[
                    0].replace('\n', '')
                occupancy = re.search(r'[0-9]+', occu).group()
            except Exception as e:
                occupancy = -1
            print "occupancy:", occupancy
            try:
                price_desc = tr.xpath('./td[contains(@class,"price")]//div[contains(@class,"hprt-price-price")]/span/text()')[0]
                price = price_desc.strip()[:-1]
                price = price.replace(',', '')
                if tax_cent == '':
                    if tr.xpath('./td[contains(@class,"price")]//div[@class="hprt-roomtype-block"]') == []:
                        tax_b = tr.xpath('.//div[contains(@class,"hptr-taxinfo-details")]')[0].text_content().split('\n')
                    else:
                        tax_b = tr.xpath('./td[contains(@class,"price")]//div[@class="hprt-roomtype-block"]')[0].text_content().split('\n')
                    tax_b = '_'.join([a for a in tax_b if a is not u''])
                    self.tax_alist = tax_b.split('不包含')
                    tax_cent, tax_other = self.tax_parse(self.tax_alist)
                    price = float(price) * (1 + tax_cent/100)
                else:
                    price = float(price) * (1 + tax_cent/100)
            except Exception as e:
                pass
            print "price:", price
            other_info['price_desc'] = other_price_desc.encode('utf-8')

            floor = -1
            try:
                "没有找到酒店层数信息"
            except:
                pass

            tax = -1
            try:
                "没有找到酒店房间关于税率的信息"
            except:
                pass

            try:
                room_id = tr.attrib.get('data-block-id', '')
                base_room_id = room_id.split('_')[0]
                source_roomid = room_id
            except Exception as e:
                source_roomid = 'NULL'
            print "room_id:", source_roomid

            if room_type and bed_type:
                self.user_datas[base_room_id] = {'room_type': room_type, 'bed_type': bed_type}
            else:
                room_type = self.user_datas[base_room_id]['room_type']
                bed_type = self.user_datas[base_room_id]['bed_type']
                print "room_type:", room_type
                print "bed_type:", bed_type
            max_select_count = -1
            try:
                max_select_count = \
                tr.xpath('./td[contains(@class,"select")]//select[contains(@class,"select")]/option/@value')[-1]
                max_select_count = int(max_select_count)
            except Exception as e:
                pass
            print "max_select_count:", max_select_count
            other_info['max_select_count'] = max_select_count

            try:
                re_ru_list_desc = tr.xpath(
                    './td[contains(@class,"conditions")]//span[contains(@class,"hprt-conditions-tooltip")]/@data-title')[
                    0]
                re_ru_list = HTML.fromstring(re_ru_list_desc)
                # 三餐
                re_ru_list = re_ru_list.xpath('./p')
                try:
                    if re_ru_list[0].text_content().replace('\n','') == '三餐:该客房房价包含所有客人的早餐。':
                        has_breakfast = 'Yes'
                        is_breakfast_free = 'Yes'
                    elif re_ru_list[0].text_content().replace('\n','') == '三餐:这间客房的房价不包括餐点。':
                        has_breakfast = 'No'
                        is_breakfast_free = 'No'
                    elif '三餐:午餐需另付，每人每天' in re_ru_list[0].text_content().replace('\n',''):
                        has_breakfast = 'No'
                        is_breakfast_free = 'No'
                    elif '三餐:早餐需另付，每人每天' in re_ru_list[0].text_content().replace('\n',''):
                        has_breakfast = 'Null'
                        is_breakfast_free = 'No'
                    elif '三餐:房价包括早餐' in re_ru_list[0].text_content().replace('\n',''):
                        has_breakfast = 'Yes'
                        is_breakfast_free = 'Yes'
                    else:
                        has_breakfast = 'Null'
                        is_breakfast_free = 'No'
                except Exception as e:
                    pass
                print "has_breakfast:", has_breakfast

                # 退改
                try:
                    return_rule = re_ru_list[1].text_content().replace('\n', '')
                    change_rule = re_ru_list[1].text_content().replace('\n', '')
                    is_cancel_free = 'Null' if u'免费' in change_rule else 'No'
                except:
                    pass

                print "return_rule:", return_rule
                print "is_cancel_free:", is_cancel_free

                # 预付款
                try:
                    # pay_method = re_ru_list[2].text_content().replace('\n', '')

                    pay_method = tr.xpath('./td[contains(@class,"conditions")]/div/ul/li/span/text()')[-1]
                    if '不退款' in pay_method:
                        pay_method = '在线支付'
                except:
                    pass
                print "pay_method:", pay_method
            except Exception as e:
                pass
            other_info['check_in_time'] = check_in_time
            other_info['check_out_time'] = check_out_time

            try:
                rest_desc = tr.xpath('./td[contains(@class,"select")]//span[contains(@class,"only_x_left")]/text()')[0]
                rest = re.search(r'[0-9]+', rest_desc).group()

            except Exception as e:
                rest = -1
            rest = int(rest)
            other_info['extra'] = {'breakfast': re_ru_list[0].text_content().replace('\n',''),
                                   'payment': pay_method,
                                   'return_rule': return_rule,
                                   'occ_des': occu.replace('\n','')}

            print "rest:", rest
            if tax_other in room_desc:
                room_desc = room_desc
            else:
                room_desc = room_desc + tax_other
            try:
                room = Room()
                room.currency = 'CNY'
                room.source = 'booking'
                room.real_source = 'booking'
                room.hotel_name = hotel_name
                room.city = cid
                room.check_in = check_in
                room.check_out = check_out
                room.source_hotelid = hotel_id
                room.room_type = room_type
                room.bed_type = bed_type
                room.room_desc = room_desc
                other_info['pay_card'] = pay_card
                other_info['review_nums'] = review_num
                other_info['img_urls'] = img_list
                room.extrabed_rule = extrabed_rule
                room.is_extrabed = is_extrabed
                room.is_extrabed_free = is_extrabed_free
                room.size = int(size)
                room.occupancy = int(occupancy)
                room.price = float(price)
                # 价格解析错误，为负数，跳过本次
                if room.price < .0:
                    continue
                room.source_roomid = source_roomid
                room.has_breakfast = has_breakfast
                room.is_breakfast_free = is_breakfast_free
                room.return_rule = return_rule
                room.change_rule = change_rule
                room.is_cancel_free = is_cancel_free
                room.pay_method = pay_method
                room.others_info = json.dumps(other_info).encode('utf-8')
                room.rest = rest
                room.floor = floor
                room.tax = tax
                room.hotel_url = 'NULL'

                if u'早餐需另付' in re_ru_list[0].text_content().replace('\n', ''):
                    room.is_breakfast_free = 'No'
                    room.has_breakfast = 'Null'

                if '支付方式以原网站为准' in room.pay_method:
                    room.pay_method = '支付方式'
                elif '需要预付' in room.pay_method and '晚房费' in room.pay_method:
                    room.pay_method = '支付方式'
                elif '无需预付' in room.pay_method:
                    room.pay_method = '到店支付'
                elif '需预付' in room.pay_method and '全额' in room.pay_method:
                    room.pay_method = '在线支付'

                room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid, \
                              room.real_source, room.room_type, room.occupancy, room.bed_type, room.size, room.floor, \
                              room.check_in, room.check_out, room.rest, room.price, room.tax, room.currency,
                              room.pay_method, \
                              room.is_extrabed, room.is_extrabed_free, room.has_breakfast, room.is_breakfast_free, \
                              room.is_cancel_free, room.extrabed_rule, room.return_rule, room.change_rule,
                              room.room_desc, \
                              room.others_info, room.guest_info)
                room_infos.append(room_tuple)
                print "others_info:", other_info
            except:
                print traceback.format_exc()
        return room_infos

    def new_parse_three_room(self, content, check_in, check_out, hotel_id, cid):
        print "进入第三种的解析"
        room_infos = []
        tree = content
        try:
            hotel_name = tree.xpath('//*[@id="hp_hotel_name"]/text()')[0].strip().encode('utf-8')
        except Exception as e:
            print 'error in line 350 meg is {0}'.format(e)
            raise parser_except.ParserException(parser_except.PROXY_INVALID, 'bookingHotel::代理异常')
        print 'hotel_name=>%s' % hotel_name
        content = HTML.tostring(content)
        try:
            city = re.findall(r"city_name: '(.*?)',", content)[0]
        except:
            city = 'NULL'
        print 'city=>%s' % city
        try:
            pay_list = tree.xpath("//div[@class='description hp_bp_payment_method']/ul")[0].text_content()
            pay_card = pay_list.replace(',', '||')
            pay_card = pay_card.replace('\n', '')
            pay_card = pay_card.encode('utf-8')
        except:
            pay_card = ''
        print "pay_card:", pay_card
        try:
            extrabed_rules = tree.xpath("//div[@class='description']/p/text()")
            # 宠物
            extrabed_rule_one = [extrabed_rules[1]] + [extrabed_rules[2]] + [extrabed_rules[4]] + [
                extrabed_rules[5]] + [extrabed_rules[6]]
            extrabed_rule = ' '.join([ex.strip() for ex in extrabed_rule_one if ex != '\n'])
            extrabed_rule = extrabed_rule.encode('utf-8')
        except:
            extrabed_rule = ''
        print 'extrabed_rule=>%s' % extrabed_rule
        try:
            if u'使用现有床铺收费' in extrabed_rule or u'一间客房增加' in extrabed_rule or u'一张加床收费' in extrabed_rule:
                is_extrabed = 'Yes'
            else:
                is_extrabed = 'No'
        except:
            pass
        print 'is_extrabed=>%s' % is_extrabed
        try:
            if u'免费加床' in extrabed_rule or u'不收费' in extrabed_rule:
                is_extrabed_free = 'Yes'
            else:
                is_extrabed_free = 'No'
        except:
            pass
        print 'is_extrabed_free=>%s' % is_extrabed_free
        check_in_time = ''
        try:
            check_in_time = tree.xpath("//span[@data-component='prc/timebar']/@data-from-label")[-1].replace('\n',
                                                                                                             '').strip().encode(
                'utf-8')
        except Exception, e:
            pass
        print 'check_in_time=>%s' % check_in_time
        check_out_time = ''
        try:
            check_out_time = tree.xpath("//span[@data-component='prc/timebar']/@data-until-label")[-1].replace('\n',
                                                                                                               '').strip().encode(
                'utf-8')
        except Exception, e:
            pass
        print 'check_out_time=>%s' % check_out_time

        try:
            review_num = tree.xpath('//p[@class="hp-gallery-rscore--desc"]')[0].text_content()
            review_num = re.search(u'[0-9]+', review_num).group()
        except:
            review_num = '0'
        print 'review_num =>%s' % review_num
        img_list = []
        try:
            for a in tree.xpath('//div/img/@src'):
                try:
                    href = a
                    if '.jpg' in href:
                        img_list.append(href)
                        if len(img_list) > 5:
                            break
                except:
                    pass
        except:
            pass
        img_list = '|'.join(img_list)
        print 'img_list=>%s' % img_list

        tr_list = tree.xpath('//ul[@class="tdot_roomstable"]/li')
        for tr in tr_list:
            room_type = ""
            bed_type = ""
            room_desc = ""
            try:
                if tr.xpath('./@class')[0] == 'in-high-demand-wrapper':
                    continue
                else:
                    room_types = tr.xpath('./div[@class="room_block_header_container"]')[0].text_content()
                if '选择床型' in room_types.replace('\n', '').encode():
                    room_type = room_types.replace('\n', ' ').split(' ')[6].encode('utf-8')
                    rest = room_types.replace('\n', ' ').split(' ')[4]
                    bed_list = []
                    for i in tr.xpath('./div[@class="room_block_header_container"]')[0].xpath('.//label'):
                        if '选择床型' in i.text_content():
                            pass
                        else:
                            bed_list.append(i.text_content().replace('\n', ''))
                    bed_type = '或'.join(bed_list)
                    room_desc = room_types.split(' ')[-1].split('\n')[-3]
                else:
                    room_type = room_types.replace('\n', ' ').split(' ')[6].encode('utf-8')
                    bed_type = room_types.replace('\n', ' ').split(' ')[26]
                    room_desc = room_types.replace('\n', ' ').split(' ')[32]
                    if '床' not in bed_type:
                        bed_type = room_types.replace('\n', ' ').split(' ')[41]
                        room_desc = room_types.replace('\n', ' ').split(' ')[-3]
            except Exception as e:
                pass
            print "room_type:", room_type
            print "bed_type:", bed_type
            print "room_desc:", room_desc

            other_info = {}
            rest = -1
            floor = -1
            try:
                "没有找到酒店层数信息"
            except:
                pass
            tax = -1
            try:
                "没有找到酒店房间关于税率的信息"
            except:
                pass
            size = -1
            try:
                "没有找到房间面积的信息"
                pass
            except Exception as e:
                pass

            try:
                tax_cent = 0
                tax_other = ''
                bed_types = \
                    tr.xpath('./div[@class="room_options_wrapper_container"]/div[@class="room_options_wrapper"]')[0]
                for bed_tp in bed_types:
                    room = Room()
                    room.currency = 'CNY'
                    room.source = 'booking'
                    room.real_source = 'booking'
                    room.hotel_name = hotel_name
                    room.city = cid
                    room.check_in = check_in
                    room.check_out = check_out
                    room.source_hotelid = hotel_id
                    room.room_type = room_type
                    room.bed_type = bed_type
                    other_info['pay_card'] = pay_card
                    other_info['review_nums'] = review_num
                    other_info['img_urls'] = img_list
                    room.extrabed_rule = extrabed_rule
                    room.is_extrabed = is_extrabed
                    room.is_extrabed_free = is_extrabed_free
                    room.size = int(size)
                    if bed_tp.xpath('./div/span')[1].text_content().replace('\n','') == '已订完':
                        continue
                    occupancy = bed_tp.xpath('./div/span/@class')[0].split(' ')[1][-1]
                    room.occupancy = int(occupancy)
                    if bed_tp.xpath('./div')[3].xpath('./span')[0].xpath('./strong') == []:
                        days = 1
                        price = re.search(u'[\d]*',bed_tp.xpath('./div')[3].xpath('./span')[0].text_content().replace('\n','').replace(',', '')).group()
                        if len(bed_tp.xpath('./div')[3].xpath('./div')) > 1:
                            tax_info = bed_tp.xpath('./div')[3].xpath('./div')[1].text_content().replace('\n', '').split('不包含')
                        else:
                            if bed_tp.xpath('./div')[3].xpath('./div') == []:
                                tax_info = ''
                            else:
                                tax_info = bed_tp.xpath('./div')[3].xpath('./div')[0].text_content().replace('\n','').split('不包含')
                        tax_cent, tax_other = self.tax_parse(tax_info)
                    else:
                        days = re.search(u'[\d]*', bed_tp.xpath('./div')[3].xpath('./span')[0].xpath('./strong')[
                            0].text_content()).group()
                        price = re.search(u'[\d]*', bed_tp.xpath('./div')[3].xpath('./span')[1].xpath('./span')[
                            0].text_content().replace('\n', '').replace(',', '')).group()
                    if price != '':
                        price = float(price) / float(days)
                    else:
                        continue
                    if tax_other in room_desc:
                        room.room_desc = room_desc
                    else:
                        room.room_desc = room_desc + tax_other
                    room.price = float(price) * (1 + tax_cent/100)
                    if room.price < .0:
                        continue
                    source_roomid = bed_tp.xpath('./@id')[0].split('-')[2]
                    room.source_roomid = source_roomid
                    foods = bed_tp.xpath('./div')[1].xpath('./p')[0].text_content().replace('\n', '')
                    if '早餐需另付' in foods:
                        has_breakfast = 'Null'
                        is_breakfast_free = 'No'
                    # elif '早餐免费' in foods:
                    #     has_breakfast = 'Yes'
                    #     is_breakfast_free = 'Yes'
                    elif '房价包括早餐' in foods:
                        has_breakfast = 'Yes'
                        is_breakfast_free = 'Yes'
                    else:
                        has_breakfast = 'No'
                        is_breakfast_free = 'No'
                    room.has_breakfast = has_breakfast
                    room.is_breakfast_free = is_breakfast_free
                    if bed_tp.xpath('./h3')[0].text_content().replace('\n','') == '':
                        continue
                    else:
                        rules = bed_tp.xpath('./div')[1].xpath('./p')[1].text_content().replace('\n', '')
                    return_rule = rules
                    change_rule = rules
                    room.return_rule = return_rule
                    room.change_rule = change_rule
                    if '免费取消期限' in rules:
                        is_cancel_free = 'Null'
                    else:
                        is_cancel_free = 'No'
                    room.is_cancel_free = is_cancel_free
                    pay_method = bed_tp.xpath('./div')[1].xpath('./p')[2].text_content().replace('\n', '')
                    room.pay_method = pay_method
                    other_info['extra'] = {'breakfast': foods,
                                           'payment': pay_method,
                                           'return_rule': return_rule,
                                           'occ_des': occupancy}
                    room.others_info = json.dumps(other_info).encode('utf-8')
                    room.rest = rest
                    room.floor = floor
                    room.tax = tax
                    room.hotel_url = 'NULL'

                    if '支付方式以原网站为准' in room.pay_method:
                        room.pay_method = '支付方式'
                    elif '需要预付' in room.pay_method and '晚房费' in room.pay_method:
                        room.pay_method = '支付方式'
                    elif '无需预付' in room.pay_method:
                        room.pay_method = '到店支付'
                    elif '需预付' in room.pay_method and '全额' in room.pay_method:
                        room.pay_method = '在线支付'

                    room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid,
                                  room.real_source, room.room_type, room.occupancy, room.bed_type, room.size,
                                  room.floor, room.check_in, room.check_out, room.rest, room.price, room.tax,
                                  room.currency, room.pay_method, room.is_extrabed, room.is_extrabed_free,
                                  room.has_breakfast,
                                  room.is_breakfast_free, room.is_cancel_free, room.extrabed_rule, room.return_rule,
                                  room.change_rule,
                                  room.room_desc, room.others_info, room.guest_info)
                    room_infos.append(room_tuple)
                    print "others_info:", other_info
            except Exception as e:
                logger.info('最后解析过程出错，检查网页是否改版')
                raise parser_except.ParserException(27, '解析出错')
        return room_infos


if __name__ == '__main__':

    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy_new

    mioji.common.spider.slave_get_proxy = simple_get_socks_proxy_new
    task = Task('bookingHotel')
    # task.content = '290467&hotel/tr/pearl-istanbul&1&20170619'# Y
    # task.ticket_info = {'cid': 1}
    task.content = '246843&hotel/it/eurostars-roma-aeterna&4&20180406'  # Y
    task.ticket_info = {'cid': 1, "room_info": [{"occ": 2, "num": 1, "room_count": 1}]}
    # task.content = '41605&hotel/ca/homewood-suites-by-hilton-r-toronto-markham&2&20171212'
    # task.content = '1030072&hotel/pl/doubletree-centre-warsaw&1&20180126'
    # task.content = '178816&hotel/au/the-travel-inn&1&20171225'
    # task.content = '1302175&hotel/it/b-amp-b-milano-san-siro&1&20171222'
    # task.content = 'NULL&hotel/jp/hilton-tokyo-bay&3&20171229'
    # task.content = '55308&hotel/fr/viator&3&20180101'
    # task.content = '50669&hotel/fr/paris-massena-olympiades&3&20180101'
    # task.content = '55308&hotel/fr/viator&3&20180101'
    # task.content = '42881&hotel/mx/fiesta-inn-monterrey-la-fe&2&20171216'
    # task.content = '76725&hotel/hk/jw-marriott-hong-kong&1&20171229'
    # task.content = '76221&hotel/ca/metropolitan-toronto&2&20180126'
    # task.content = "1669712&hotel/us/the-park-ave-north-new-york&1&20180122"

    spider = BookingSpider(task)
    res = spider.crawl()
    print res
    print spider.result