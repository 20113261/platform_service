# coding: utf-8
consumer = """consumer_address	消费地址
open_time	营业时间
take_ticket_time	取票时间
take_ticket_address	取票地点
take_ticket_credentials	出示证件
perform_time	表演时间
perform_period	表演时长
depart_time	出发时间
depart_address	出发地点
visit_time	游览时间
visit_period	游览时长
ride_time	乘坐时间
repast_time	就餐时间
repast_period	就餐时长
consumer_period	消费时长
transfer_time	接送时间
transfer_address	接送地点
dress_code	着装建议
Period_of_validity	有效期
other	其它
remark	备注"""
consumer = consumer.split('\n')
"""
把字符串中英文名字换成中文名字
"""


def get_cn_consumer(str_consumer):

    dic = {}
    for i in consumer:
        ls = i.split('\t')
        dic[ls[0]] = ls[1]
    for i in dic:
        str_consumer = str_consumer.replace(i, dic[i])
    return str_consumer
