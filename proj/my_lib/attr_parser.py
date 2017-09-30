# coding:utf-8
from __future__ import absolute_import

import sys

reload(sys)
sys.setdefaultencoding('utf-8')

import re, json
import urlparse
from proj.my_lib import db_localhost
from lxml import html
from pyquery import PyQuery
from proj.my_lib.Common.Browser import MySession
from common.common import get_proxy
from util.UserAgent import GetUserAgent
from proj.my_lib.Common.Utils import try3times
from proj.my_lib.Common.Utils import all_chinese, has_chinese

from proj.my_lib.decode_raw_site import decode_raw_site

img_get_url = 'http://www.tripadvisor.cn/LocationPhotoAlbum?detail='
'mysql+pymysql://mioji_admin:mioji1109@10.10.228.253:3306/base_data?charset=utf8'

pattern = re.compile('\{\'aHref\'\:\'([\s\S]+?)\'\,\ \'')


@try3times(try_again_times=10)
def image_parser(detail_id):
    with MySession(need_proxies=True, need_cache=True) as session:
        page = session.get(urlparse.urljoin(img_get_url, detail_id))
        root = PyQuery(page.text)
        images_list = []
        for div in root('.photos.inHeroList div').items():
            images_list.append(div.attr['data-bigurl'])
        img_list = '|'.join(images_list)
        assert img_list != '' or img_list is not None, 'NO IMAGES'
        return img_list


# m@d
# def get_site_encode_string(content):
#     root = html.fromstring(content)
#     items = root.find_class('fl')
#     result = ''
#     for item in items:
#         link_item = item.find_class('taLnk')
#         if len(link_item) != 0:
#             try:
#                 onclick_text = link_item[0].xpath('./@onclick')[0]
#                 if "ta.util.link.targetBlank" in onclick_text:
#                     result = pattern.findall(onclick_text)[0]
#                     break
#             except:
#                 continue
#     return result


def parse(content, url, city_id, debug=False):
    result = []
    try:
        content = content.decode('utf8')
    except:
        return "Error"
    root = html.fromstring(content)

    # id等信息,source_id, source_city_id, soruce
    source = 'daodao'
    source_id = re.compile(r'd(\d+)').findall(url)[0]
    source_city_id = re.compile(r'g(\d+)').findall(url)[0]
    print 'source_id: %s' % source_id

    # source_id = rest_id
    map_info = ''
    try:
        map_pat = re.compile(r"taStore.store\('typeahead.recentHistoryList', (.*?)\);", re.S)
        poi_data = json.loads(map_pat.findall(content)[0])

        def find_mapinfo(node):
            try:
                if source_id == str(node.get('value', 'NULL')):
                    tmp_map = node.get('coords', None)
                    if tmp_map:
                        tmp_map = ','.join(tmp_map.split(',')[::-1])
                    return tmp_map
            except:
                pass
            # 没有的话找子节点
            child_list = node.get('urls', [])
            if child_list:
                for poi_info in child_list:
                    tmp_map = find_mapinfo(poi_info)
                    if tmp_map:
                        return tmp_map

        for poi_list in poi_data:
            map_info = find_mapinfo(poi_list)
            if map_info:
                break
    except:
        map_info = ''

    if len(content) < 2000:
        print('no content')
        return "Error"

    # 名字 name,name_en
    name = ''
    name_en = ''
    try:
        name = root.xpath('//*[@class="heading_title"]/text()')[0]
    except Exception as e:
        pass

    try:
        name_en = root.xpath('//*[@class="heading_title"]/*[@class="altHead"]/text()')[0]
    except Exception as e:
        pass

    if name and name_en:
        pass
    elif name or name_en:
        if name:
            name_key = name
        else:
            name_key = name_en

        # 确定中英文名
        if has_chinese(name):
            name = name_key
            name_en = ''
        else:
            name = ''
            name_en = name_key
    else:
        # todo new func to get name
        pass

    # 排除已经停业的 POI
    name_test_case = ''
    try:
        name_test_case = root.find_class('heading_title')[0].text_content().encode('utf-8').strip()
    except Exception as e:
        pass

    if name_test_case.find('停业') > -1 or name_test_case.find('移除') > -1:
        name = name_en = '停业'

    # 地址address
    try:
        address = ''
        # m@ 更新 address = root.find_class('format_address')[0].text_content().strip().encode('utf-8').replace('地址: ', '')
        address = root.find_class('blEntry address')[0].text_content().strip().encode('utf-8')



    except Exception, e:
        address = ''
        # traceback.print_exc(e)
    print 'address: %s' % address

    # 电话tel
    try:
        # m@ 更新 tel = root.find_class('phoneNumber')[0].text
        tel = root.find_class('blEntry phone')[0].text_content()
        if not re.search(r'[0-9]+',tel):
            tel = ''
    except:
        tel = ''
    print 'tel: %s' % tel

    # m@add 官网url
    site = ''
    try:
        site_data = root.find_class('blEntry website')[0].attrib['data-ahref']
        site = decode_raw_site(site_data)
    except Exception, e:
        print(e)

    # 排名rank
    try:
        rank = ''
        # m@ rank_text = root.find_class('slim_ranking')[0].text_content().encode('utf-8').replace(',', '')
        rank_text = root.find_class('rating_and_popularity')[0].text_content().strip()

        nums = re.compile(r'(\d+)', re.S).findall(rank_text)
        # rank = nums[0] + '/' + nums[1]
        rank = nums[-1]
    except Exception, e:
        rank = ''
    print 'rank: %s' % rank

    # 评分rating
    try:
        # m@ if len(root.find_class('rs rating')) != 0:
        # class from 'rs rating' to 'rating'
        if root.find_class('rating'):
            grade_temp = root.find_class('rating')[0]
            rating = float(grade_temp.xpath('//span[@class="overallRating"]')[0].text_content())
            reviews = int(re.search('\d+', grade_temp.text_content().replace(',', '')).group())
        else:
            rating = -1
            reviews = -1
    except Exception, e:
        # traceback.print_exc(e)
        rating = -1
        reviews = -1
    print 'rating: %s' % rating
    print 'reviews: %s' % reviews

    # try:
    #     if reviews > 10:
    #         urls = []
    #         for offset in range(10, reviews, 10):
    #             next_url = url.replace('Reviews', 'Reviews-or%s' % offset)
    #             urls.append((next_url, source_id, int(offset) / 10, miaoji_id))
    #             if offset > 100:
    #                 break
    #             print 'insert paging', insert_paging(urls)
    # except Exception, e:
    #     # print str(e)
    #     pass
    #
    # print 'rating: %s' % rating
    # print 'reviews: %s' % reviews

    # 开店时间 open_time
    try:
        open_time = root.find_class('hoursAll')[0].text_content()

    except:
        open_time = ''

    if not open_time:
        try:
            days = []
            hours = []
            if len(root.find_class('hoursOverlay')) != 0:
                for i in root.find_class('hoursOverlay')[0].find_class('days'):
                    if len(i.xpath('text()')) != 0:
                        days.append(i.xpath('text()')[0].encode('utf-8').strip())
                for j in root.find_class('hoursOverlay')[0].find_class('hours'):
                    if len(j.xpath('text()')) != 0:
                        hours.append(j.xpath('text()')[0].encode('utf-8').strip())
            time = ''
            for n in range(len(days)):
                time += days[n]
                time += ':'
                time += hours[n]
                if (n != len(days) - 1):
                    time += '|'
            if time != '':
                open_time = time
            else:
                open_time = ''
        except Exception, e:
            # traceback.print_exc(e)
            open_time = ''
    print 'open_time: %s' % open_time

    # tagid
    tagid = ''
    try:
        tagid = root.find_class('header_detail attraction_details')[0] \
            .xpath('div')[0].text_content().strip().encode('utf-8').split('\n')[-1].replace(',', '|')
    except Exception, e:
        tagid = ''
    print 'tagid: %s' % tagid
    tag = tagid

    try:
        recommended_time = ''
        for i in root.xpath('//*[@class="detail"]'):
            info = i.text_content().encode('utf-8').strip()
            try:
                if info.find('建议游览时间') > -1:
                    recommended_time = info.split('：')[1].strip()
            except:
                recommended_time = ''
    except:
        recommended_time = ''
    print 'recommended_time: %s' % recommended_time

    try:
        desc = root.xpath('//*[@id="OVERLAY_CONTENTS"]')[0].text_content().encode('utf-8').strip()
    except:
        try:
            desc = root.xpath('//*[@class="description"]/*[@class="text"]')[0].text_content().encode('utf-8').strip()
        except:
            desc = ''
    print 'desc: %s' % desc

    # 卓越奖
    prize = 0
    try:
        icon_prize = root.find_class('ui_icon certificate-of-excellence')
        if icon_prize:
            prize = 1
        else:
            test = root.find_class('taLnk text')
            if len(test) > 0:
                prize = 1
    except:
        pass

    # 旅行家标志
    traveler_choice = 0

    img_tcAward = root.find_class('tcAward')
    if img_tcAward:
        traveler_choice = 1
    else:
        test = root.find_class('tchAward')
        if len(test) > 0:
            traveler_choice = 1

    # 图片抓取
    if not debug:
        try:
            detail_id = source_id
            image_urls = image_parser(detail_id)
        except:
            image_urls = ''
    else:
        image_urls = ''

    # if image_urls == '':
    #     raise Exception('NO IMAGES')

    # 第一条评论的review id 用于没有介绍时使用
    try:
        raw_onclick = root.find_class('reviewSelector')[1].xpath('./@id')[0]
        first_review_id = re.findall('review_(\d+)', raw_onclick)[0]
    except:
        first_review_id = ''

    print "source_city_id: ", source_city_id
    print "url: ", url

    # city_id = 'NULL'
    # try:
    #     loc = root.find_class('breadcrumb')
    #     country = loc[0].text_content().strip()
    #     state = loc[1].text_content().strip()
    #     city = loc[3].text_content().strip()
    # except:
    #     pass

    #
    # encode_string = get_site_encode_string(content)

    # print "encode_string: ", encode_string

    # raw_site = ''
    # if encode_string != '':
    #     raw_site = decode_raw_site(encode_string)
    #
    # print "raw_site: ", raw_site

    result = {
        'source': source,
        'name': name,
        'name_en': name_en,
        'phone': tel,
        'map_info': map_info,
        'address': address,
        'opentime': open_time,
        'grade': rating,
        'ranking': rank,
        'tagid': tagid,
        'commentcounts': reviews,
        'recommended_time': recommended_time,
        'introduction': desc,
        'prize': prize,
        'traveler_choice': traveler_choice,
        'first_review_id': first_review_id,
        'imgurl': image_urls,
        'site': site,
        'id': source_id,
        'source_city_id': source_city_id,
        'url': url}
    return result


def insert_db(result, city_id):
    result['city_id'] = city_id
    db_localhost.insert('attr', **result)
    # sql = "insert into tp_attr_basic (`source`, `name`, `name_en`, `phone`, `map_info`, `address`, `opentime`, `star`, `ranking`, `tagid`, `commentcounts`, `recommended_time`, `introduction`, `prize`, `traveler_choice`, `first_review_id`, `imgurl`,`miaoji_id`, `id`, `source_city_id`, `url`, `site_raw`, `site_before_301`, `city_id`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    # result = list(result)
    # result.append(city_id)
    # return db.ExecuteSQL(sql, tuple(result))


if __name__ == '__main__':
    # url = 'https://www.tripadvisor.cn/Attraction_Review-g143034-d108754-Reviews-Nahuku_Thurston_Lava_Tube-Hawaii_Volcanoes_National_Park_Island_of_Hawaii_Hawaii.html'
    # url = 'https://www.tripadvisor.cn/Attraction_Review-g298490-d8514477-Reviews-Triumphal_Arch-Blagoveshchensk_Amur_Oblast_Far_Eastern_District.html'
    url = 'https://www.tripadvisor.cn/Attraction_Review-g60742-d105015-Reviews-Thomas_Wolfe_Memorial-Asheville_North_Carolina.html'
    url = 'https://www.tripadvisor.cn/Attraction_Review-g187147-d188151-Reviews-Eiffel_Tower-Paris_Ile_de_France.html'
    url = 'https://www.tripadvisor.cn/Attraction_Review-g1024140-d10000541-Reviews-Castaway_Yoga-Ko_Lipe_Satun_Province.html'
    url = 'https://www.tripadvisor.cn//Attraction_Review-g297524-d314609-Reviews-Darwin_Bay-Genovesa_Galapagos_Islands.html,https://www.tripadvisor.cn//Attraction_Review-g297524-d314610-Reviews-Darwin_Trail-Genovesa_Galapagos_Islands.html'
    url = 'https://www.tripadvisor.cn/Attraction_Review-g187147-d188150-Reviews-Musee_d_Orsay-Paris_Ile_de_France.html'
    import requests

    content = requests.get(url).content
    a = '阿什顿发斯蒂芬'
    result = parse(content, url, a)
    print json.dumps(result, ensure_ascii=False)
    # insert_db(result, 10086)
