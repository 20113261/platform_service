#!/usr/bin/env python
# -*- coding: utf-8 -*-

import traceback
import threading
import dataset

import simplejson as json

from Queue import Queue
from huantaoyouAPI import HuantaoyouApi
from util import UnFinishedSet, SkipException
from mongo import get_collection, get_ref_poi

with open('wanle') as fp:
    all_tickets = json.load(fp)

local_queue = Queue()

for item in all_tickets:
    local_queue.put(item)

print 'local queue size is', local_queue.qsize()
finish_set = set()

spider_base = dataset.connect('mysql://mioji_admin:mioji1109@10.10.230.206/tmp?charset=utf8')
tickets_fun = spider_base['tickets_fun']
view_ticket = spider_base['view_ticket']    # 门票 3
activity_ticket = spider_base['activity_ticket']   # 当地美食 1  休闲娱乐 2
tour_ticket = spider_base['tour_ticket']   # 一日游  4
play_ticket = spider_base['play_ticket']    #

# 导出命令
# mongoexport --type=csv -f id,pid,sid,name,info,ccy,price,times,date,book_pre,enter_pre,ctime,utime,ticket_type,max,min,agemin,agemax,ticket_3rd,traveller_3rd, id_3rd -d huantaoyou -c tickets_fun -o ./tickets_fun.csv
# mongoexport --type=csv -f id,pid,ptid,poi_mode,ref_poi,name,enname,city_id,addr,map_info,first_img,date,times,book_pre,enter_pre,img_list,jiesong_type,jiesong_poi,info,ctime,utime,ticket_3rd,tag,id_3rd -d huantaoyou -c play_ticket -o ./play_ticket.csv
# mongoexport --type=csv -f id,pid,ptid,poi_mode,ref_poi,name,enname,city_id,addr,map_info,first_img,img_list,date,times,book_pre,enter_pre,jiesong_type,jiesong_poi,info,ctime,utime,ticket_3rd,tag,id_3rd -d huantaoyou -c activity_ticket -o ./activity_ticket.csv
# mongoexport --type=csv -f id,pid,ptid,poi_mode,ref_poi,name,enname,city_id,addr,map_info,first_img,img_list,date,times,book_pre,enter_pre,jiesong_type,jiesong_poi,info,ctime,utime,ticket_3rd,tag,id_3rd -d huantaoyou -c tour_ticket -o ./tour_ticket.csv
# mongoexport --type=csv -f id,pid,ptid,poi_mode,ref_poi,name,enname,city_id,addr,map_info,first_img,img_list,date,times,book_pre,enter_pre,jiesong_type,jiesong_poi,info,ctime,utime,ticket_3rd,tag,id_3rd -d huantaoyou -c view_ticket -o ./view_ticket.csv
tickets_fun = get_collection('tickets_fun')
view_ticket = get_collection('view_ticket')    # 门票 3
activity_ticket = get_collection('activity_ticket')   # 当地美食 1  休闲娱乐 2
tour_ticket = get_collection('tour_ticket')   # 一日游  4
play_ticket = get_collection('play_ticket')    #
attractions = get_collection('found_attraction')
raw_data = get_collection('raw')

type_dict = {
    'activity_ticket': activity_ticket,
    'play_ticket': play_ticket,
    'view_ticket': view_ticket,
    'tour_ticket': tour_ticket
}


city_relation = {}
with open('city_relation') as city_fd:
    city_list = json.load(city_fd)
    for city in city_list:
        if 'mioji_id' in city:
            city_relation[city['city_id']] = int(city['mioji_id'])


def get_city_id(my_id):
    if my_id in city_relation:
        return city_relation[my_id]
    return 'NotFound_' + str(my_id)

'''
交通接驳 set([9])
当地美食 set([1])
当地住宿 set([106])
休闲娱乐 set([2])
门票 set([3])
一日游 set([4])

当地美食 1   view_ticket_analysis
休闲娱乐 2   view_ticket_analysis
门票 3      view_ticket_analysis
一日游 4    tour_ticket_analysis
'''

local_set = UnFinishedSet()


def insert(name, val):
    mongo['huantaoyou'][name].insert(val)


def do_work(local_api):
    current_task = local_queue.get()
    local_id = current_task['id']
    print local_id

    try:
        api_resp = local_api.get_json(local_id)
        raw_data.insert(api_resp)
        type_ret = local_api.type_classification(local_id, api_resp)
    except SkipException:
        return
    except:   # 把任务放回队列
        traceback.print_exc()
        print 'id', local_id, '获取信息失败'
        if local_id not in local_set:
            local_set.add(local_id)
            local_queue.put(current_task)
        return

    try:     # 重新入库  1 录 ticket  2 录 不同种类的数据 （3张表）  3 录 play ticket
        for key, val in type_ret.items():
            if val:
                ticket_ret = local_api.tickets_fun_analysis(local_id, val, api_resp)
                insert_ticket(ticket_ret)
                if key in ('view_ticket', 'activity_ticket', 'tour_ticket'):
                    insert_type_info(key, val)
                else:
                    insert_play_ticket(val)
        
    except SkipException:
        return
    except:  # 重新入库
        traceback.print_exc()
    return


def insert_ticket(ticket):
    ticket['sid'] = str(ticket['sid'])
    ticket['ticket_3rd'] = str(ticket['ticket_3rd'])
    tickets_fun.insert(ticket)
    insert_sql(ticket, 'tickets_fun')


def insert_type_info(type_, info):
    table = type_dict[type_]
    info['city_id'] = get_city_id(info['city_id'])
    table.insert(info)
    insert_sql(info, type_)


def insert_play_ticket(info):
    info['city_id'] = get_city_id(info['city_id'])
    play_ticket.insert(info)
    insert_sql(info, 'play_ticket')


def insert_sql(info, type_):
    del info['__type']
    del info['_id']
    keys = ['img_list', 'info', 'jiesong_poi', 'times']
    for key in keys:
        if key in info:
            info[key] = json.dumps(info[key], ensure_ascii=False)
    str_to_num_keys = ['id', 'book_pre', 'enter_pre', 'ticketType', 'agemax', 'agemin', 'max', 'min', 'id_3rd']
    for key in str_to_num_keys:
        if key in info:
            info[key] = int(info[key])
    if 'price' in info:
        info['price'] = float(info['price'])
    spider_base[type_].insert(info)


def main():
    api_instance = HuantaoyouApi()
    while not local_queue.empty():
        do_work(api_instance)
    print "done1"


def thread_run(api):
    while local_queue.qsize() > 0:
        do_work(api)


def test_entry(local_id):
    api = HuantaoyouApi()
    api_resp = api.get_json(local_id)
    try:
        type_ret = api.type_classification(local_id, api_resp)
    except:
        print json.dumps(api_resp, ensure_ascii=False)
        traceback.print_exc()
    print json.dumps(type_ret, indent=2, ensure_ascii=False)
    import pdb
    pdb.set_trace()


def using_thread():
    thread_list = []  # 线程存放列表
    for i in xrange(4):
        api_instance = HuantaoyouApi()
        t = threading.Thread(target=thread_run, args=(api_instance,))
        t.setDaemon(True)
        thread_list.append(t)

    for t in thread_list:
        t.start()

    for t in thread_list:
        t.join()

    print local_set.left_id()


if __name__ == '__main__':
    using_thread()
    # main()
    # test_entry(11830)
