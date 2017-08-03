# coding=utf-8
import sys
import pdb
import pyquery
import re

reload(sys)
sys.setdefaultencoding('utf8')

from data_obj import Qyer, DBSession


def page_parser(content, target_url):
    #pdb.set_trace()
    doc = pyquery.PyQuery(content)
    qyer = Qyer()
    try:
        qyer.id = re.findall(r'PID :\'(\d+)\'', content)[0]
    except:
        pass
    try:
        qyer.source_city_id = re.findall(r'PLACE\.CITYID = "(\d+)";', content)[0]
    except:
        pass
    qyer.source = 'qyer'
    qyer.name = doc('.cn').text()
    qyer.name_en = doc('.en').text()
    qyer.map_info = doc('meta[@property="og:location:longitude"]').attr.content + ',' + doc(
        'meta[@property="og:location:latitude"]').attr.content
    qyer.star = len(doc('.poi-stars>.single-star.full')) + 0.5 * len(doc('.poi-stars>.single-star.half'))
    qyer.grade = doc('.points>.number').text()
    qyer.ranking = re.findall(r'(\d+)', doc('.infos .rank').text())[-1]
    qyer.beentocounts = doc('.golden').text()
    if qyer.beentocounts:
        qyer.beentocounts = int(qyer.beentocounts)
    else:
        qyer.beentocounts = -1
    # qyer tips

    for item in doc('.poi-tips>li').items():
        tip_title = item('.title').text()
        tip_content = item('.content').text()
        if '门票' in tip_title:
            qyer.price = tip_content
        if '到达方式' in tip_title:
            qyer.wayto = tip_content
        if '开放时间' in tip_title:
            qyer.opentime = tip_content.replace('\n', ',')
        if '营业时间' in tip_title:
            qyer.opentime = tip_content
        if '地址' in tip_title:
            qyer.address = tip_content.replace('(查看地图)', ' ').strip()
        if '电话' in tip_title:
            qyer.phone = tip_content
        if '网址' in tip_title:
            qyer.site = tip_content
        if '所属分类' in tip_title:
            qyer.tagid = tip_content

    qyer.introduction = doc('.poi-detail').text()
    qyer.tips = doc('.poi-tipContent>.content').text()

    try:
        header = doc('.infos .rank').text().strip()
        if header.find('购物') > -1:
            qyer.cateid = '购物'
        elif header.find('美食') > -1:
            qyer.cateid = '美食'
        elif header.find('景点') > -1:
            qyer.cateid = '景点'
        elif header.find('活动') > -1:
            qyer.cateid = '活动'
        elif header.find('交通') > -1:
            qyer.cateid = '交通'
        else:
            qyer.cateid = '其他'
    except:
        pass

    try:
        qyer.commentcounts = re.findall(r'(\d+)', doc('.summery').text())[0]
    except:
        pass

    qyer.url = target_url

    return qyer


if __name__ == '__main__':
    import requests


    target_url = 'http://place.qyer.com/poi/V2IJYVFlBzdTZg/'
    page = requests.get(target_url)
    page.encoding = 'utf8'
    content = page.text
    with open('content.txt','w+') as temp:
        temp.write(content)
    result = page_parser(content, target_url)
    try:
        session = DBSession()
        session.merge(result)
    except Exception as e:
       print e
    else:
        session.commit()
    finally:
        session.close()
