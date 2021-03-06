# coding=utf-8
from __future__ import print_function
import sys
import pdb
import pyquery
import re
import json
import traceback
import time
import pprint

reload(sys)
sys.setdefaultencoding('utf8')

from proj.my_lib import db_localhost
from data_obj import Qyer, DBSession
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.Common.Utils import retry
from lxml import html as HTML
import re
import json

comment_counts_url = 'http://place.qyer.com/poi.php?action=starlevel'
comment_url = 'http://place.qyer.com/poi.php?action=comment&page=1&order=5&poiid=57110&starLevel=all&_=1494983732352'


@retry(times=10, raise_exc=False)
def parse_comment_counts(poi_id):
    with MySession(need_proxies=True, need_cache=True) as session:
        start_level = session.post(comment_counts_url, data={'poiid': poi_id})
        comment_counts = json.loads(start_level.text).get('data', {}).get('all', -1)
        if int(comment_counts) == -1:
            raise Exception()
    return comment_counts


@retry(times=10, raise_exc=False)
def parse_image_urls(target_url):
    with MySession(need_proxies=True, need_cache=True) as session:
        image_page = session.get(target_url + '/photo').content.decode('utf8')
        page = pyquery.PyQuery(image_page)

        content = HTML.tostring(page[0])
        counts = re.search(r'var data = (.*)(?=;)', content).group(1)
        counts = json.loads(counts)
        beentocounts = counts.get('counts', {}).get('beentocounts', -1)
        plantocounts = counts.get('counts', {}).get('plantocounts', -1)

        ul = page('.pla_photolist.clearfix li')
        img_list = [li('._jsbigphotoinfo img').attr('src').rstrip('/180180') for li in ul.items()]

        try:
            # 当有翻页时正常执行后面
            page_count = page[0].xpath('//h2[@class="pla_bigtit fontYaHei"]/text()')[0]
            page_count = re.search(u'[0-9]+', page_count).group()
            pages = int(page_count) / 30
        except Exception:
            # 当无翻页时直接返回
            return '|'.join(img_list), beentocounts, plantocounts

    if pages >= 3:
        pages = 4
    for page in range(int(pages) + 2):
        with MySession(need_proxies=True, need_cache=True) as img_session:
            image_page = img_session.get(target_url + '/photo/page{0}'.format(page)).content.decode('utf8')
            page = pyquery.PyQuery(image_page)
            ul = page('.pla_photolist.clearfix li')
            img_list.extend([li('._jsbigphotoinfo img').attr('src').rstrip('/180180') for li in ul.items()])

    return '|'.join(img_list), beentocounts, plantocounts


# def parse_comment(qyer):
#     params = {
#         'page': 1,
#         'order': 5,
#         'poiid': qyer.id,
#         'starLevel': 'all',
#         '_': time.time() * 1000,
#     }
#     json_data = json.loads(ss.get(comment_url, params=params).content.decode('utf-8'))
#
#     # pprint.pprint(json_data)
#
#     for item in json_data.get('data', {}).get('lists', []):
#         comment = {
#             'source': 'qyer',
#             'source_city_id': qyer.source_city_id,
#             'source_id': qyer.id,
#             'miaoji_id': 'NULL',
#             'language': 'zhCN',
#             'review_id': item.get('id'),
#             'review_text': item.get('content').encode('utf8'),
#             'review_link': item.get('link'),
#             'comment_time': item.get('date'),
#             # 'review_id': item.get('id'),
#             'comment_rating': item.get('starlevel'),
#             'user_name': item.get('userinfo', {}).get('name'),
#             'user_link': item.get('userinfo', {}).get('link'),
#         }
#         # comment.comment_rating = item.get('userinfo', {}).get('name')
#
#         db_localhost.insert_mb4('tp_comment_0814', **comment)


def page_parser(content, target_url):
    # pdb.set_trace()
    doc = pyquery.PyQuery(content)
    qyer = Qyer()
    try:
        qyer.id = re.findall(r'PID :\'(\d+)\'', content)[0]
    except Exception as e:
        print(traceback.format_exc(e))
    try:
        qyer.source_city_id = re.findall(r'PLACE\.CITYID = "(\d+)";', content)[0]
    except Exception as e:
        print(traceback.format_exc(e))

    try:
        qyer.source = 'qyer'
        qyer.name = doc('.cn').text()
        qyer.name_en = doc('.en').text()
        qyer.map_info = doc('meta[@property="og:location:longitude"]').attr.content + ',' + doc(
            'meta[@property="og:location:latitude"]').attr.content
        qyer.star = len(doc('.poi-stars>.single-star.full')) + 0.5 * len(doc('.poi-stars>.single-star.half'))
        if qyer.star == 0:
            qyer.star = -1
        qyer.grade = doc('.points>.number').text()
        qyer.ranking = re.findall(r'(\d+)', doc('.infos .rank').text())[-1]
        qyer.beentocounts = doc('.golden').text()
        if qyer.beentocounts:
            qyer.beentocounts = int(qyer.beentocounts)
        else:
            qyer.beentocounts = -1
    except Exception as e:
        print(target_url)
        print(traceback.format_exc(e))

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
            # if '所属分类' in tip_title:
            #     qyer.tagid = tip_content

    try:
        tag_tag = """<!-- 需要隐藏所属分类 -->"""
        tag_start_index = content.find(tag_tag) + 52
        assert tag_start_index >= 52, '什么都没找到'
        tag_end_index = content.find('-->', tag_start_index)
        tag = pyquery.PyQuery(content[tag_start_index:tag_end_index])
        qyer.tagid = tag.text()[6:]
    except Exception as e:
        print(traceback.format_exc(e))

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
    except Exception as e:
        print(traceback.format_exc(e))

    try:
        # qyer.commentcounts = re.findall(r'(\d+)', doc('.summery').text())[0]
        comment_counts = parse_comment_counts(qyer.id)
        if comment_counts:
            qyer.commentcounts = int(comment_counts)
        else:
            qyer.commentcounts = -1
    except Exception as e:
        qyer.commentcounts = -1
        print(traceback.format_exc(e))

    # try:
    #     parse_comment(qyer)
    # except Exception as e:
    #     print(traceback.format_exc(e))

    qyer.url = target_url

    try:
        qyer.imgurl, qyer.beentocounts, qyer.plantocounts = parse_image_urls(target_url)
    except Exception as e:
        print(traceback.format_exc(e))

    print(qyer)
    return qyer


if __name__ == '__main__':
    # import requests
    #
    # target_url = 'http://place.qyer.com/poi/V2AJZVFlBzNTYVI2/'
    # # target_url = 'http://place.qyer.com/poi/V2cJYFFvBzdTYQ/'
    # target_url = 'http://place.qyer.com/poi/V2cJa1FkBzNTbA/'
    # target_url = 'http://place.qyer.com/poi/V2cJYFFhBzJTZQ/'
    # target_url = 'http://place.qyer.com/poi/V2cJYFFhBz5TZA/'
    # target_url = 'http://place.qyer.com/poi/V2AJYVFmBzRTZg/'
    # target_url = 'http://place.qyer.com/poi/V2YJY1FjBz5TZFI9/'
    # target_url = 'http://place.qyer.com/poi/V2UJY1FnBzZTZFI5/'
    # target_url = 'http://place.qyer.com/poi/V2wJYVFuBzFTZQ/'
    # page = requests.get(target_url)
    # page.encoding = 'utf8'
    # content = page.text
    # # with open('content.txt','w+') as temp:
    # #     temp.write(content)
    # result = page_parser(content, target_url)
    # for k, v in result.__dict__.items():
    #     print('%s : %s' % (k, v))
    #
    # print(len(result.__dict__.keys()))
    # print(parse_comment_counts("200832"))

    # target_url = 'http://place.qyer.com/poi/V2AJZVFlBzNTYVI2/'
    # # target_url = 'http://place.qyer.com/poi/V2cJYFFvBzdTYQ/'
    # target_url = 'http://place.qyer.com/poi/V2cJa1FkBzNTbA/'
    # target_url = 'http://place.qyer.com/poi/V2cJYFFhBzJTZQ/'
    # target_url = 'http://place.qyer.com/poi/V2cJYFFhBz5TZA/'
    # target_url = 'http://place.qyer.com/poi/V2AJYVFmBzRTZg/'
    # target_url = 'http://place.qyer.com/poi/V2YJY1FjBz5TZFI9/'
    # import requests
    # target_url = 'http://place.qyer.com/poi/V2UJYVFjBzFTZlI9/'
    # target_url = 'http://place.qyer.com/poi/V2UJYVFkBzBTbFI9CmU/'
    # page = requests.get(target_url)
    # page.encoding = 'utf8'
    # content = page.text
    # # # with open('content.txt','w+') as temp:
    # # #     temp.write(content)
    # result = page_parser(content, target_url)
    # for k, v in result.__dict__.items():
    #     print('%s : %s' % (k, v))
    #
    # print(len(result.__dict__.keys()))

    # try:
    #     session = DBSession()
    #     session.merge(result)
    # except Exception as e:
    #    print e
    # else:
    #     session.commit()
    # finally:
    #     session.close()

    print(parse_image_urls('http://place.qyer.com/poi/V2UJYlFvBzZTZlI6/'))
