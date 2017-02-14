# coding=utf-8
from __future__ import absolute_import

import json
import re

import db_localhost
from lxml import html

from .decode_raw_site import decode_raw_site

pattern = re.compile('\{\'aHref\'\:\'([\s\S]+?)\'\,\ \'')
db = db_localhost


def has_chinese(contents, encoding='utf-8'):
    zh_pattern = re.compile(u'[\u4e00-\u9fa5]+')
    if not isinstance(contents, unicode):
        u_contents = unicode(contents, encoding=encoding)
    results = zh_pattern.findall(u_contents)
    if len(results) > 0:
        return True
    else:
        return False


def image_paser(content, url):
    dom = html.fromstring(content)
    result = ''
    if len(dom.find_class('flexible_photo_wrap')) != 0:
        try:
            raw_text = dom.find_class('flexible_photo_album_link')[0].find_class('count')[0].xpath('./text()')[0]
            image_num = re.findall('\((\d+)\)', raw_text)[0]
            pattern = re.compile('var lazyImgs = ([\s\S]+?);')
            google_list = []
            img_url_list = []
            if len(pattern.findall(content)) != 0:
                for each_img in json.loads((pattern.findall(content)[0]).replace('\n', '')):
                    img_url = each_img[u'data']
                    if 'ditu.google.cn' in img_url:
                        google_list.append(img_url)
                    elif 'photo-' in img_url:
                        img_url_list.append(img_url.replace('photo-l', 'photo-s').replace('photo-f', 'photo-s'))

            result = '|'.join(img_url_list[:int(image_num)])
            print 'image_urls: ', result
        except:
            try:
                image_num = len(dom.find_class('flexible_photo_wrap'))
                pattern = re.compile('var lazyImgs = ([\s\S]+?);')
                google_list = []
                img_url_list = []
                if len(pattern.findall(content)) != 0:
                    for each_img in json.loads((pattern.findall(content)[0]).replace('\n', '')):
                        img_url = each_img[u'data']
                        if 'ditu.google.cn' in img_url:
                            google_list.append(img_url)
                        elif 'photo-' in img_url:
                            img_url_list.append(img_url.replace('photo-l', 'photo-s').replace('photo-f', 'photo-s'))
                result = '|'.join(img_url_list[:image_num])
            except:
                pass
    return result


def get_site_encode_string(content):
    root = html.fromstring(content)
    items = root.find_class('fl')
    result = ''
    for item in items:
        link_item = item.find_class('taLnk')
        if len(link_item) != 0:
            try:
                onclick_text = link_item[0].xpath('./@onclick')[0]
                if "ta.util.link.targetBlank" in onclick_text:
                    result = pattern.findall(onclick_text)[0]
                    break
            except:
                continue
    return result


def parse(content, url, miaoji_id='NULL'):
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

    if len(content) < 2000:
        print 'no content'
        return "Error"

    # 名字 name,name_en
    try:
        name_en = root.find_class('heading_name_wrapper')[0].text_content().encode('utf-8').strip().split('\n')[1]
    except:
        name_en = ''

    try:
        try:
            name = root.find_class('heading_name_wrapper')[0].text_content().encode('utf-8').strip()
        except:
            name = root.get_element_by_id('HEADING').text_content().encode('utf-8').strip()
        if len(name.split('\n')) > 1:
            if name.find('停业') > -1 or name.find('移除') > -1:
                print 'stop:', source_id, '\t', url
                raise Exception
            else:
                name = name.split('\n')[0]
    except Exception, e:
        name = ''
        print 'name error', url
        # print str(e)
        # 若出错则返回空的list
        return "Error"

    if name == '' and name_en != '':
        name = name_en
    if name == '' and name_en == '':
        print 'no name'
        # return rest_info
    if name_en == '':
        if not has_chinese(name):
            name_en = name
        else:
            name_en = ''
    # 如果name是英文，则name_en=name
    if not has_chinese(name):
        name_en = name

    # 经纬度map_info
    try:
        map_info = ''
        if not map_info:
            try:
                lng = root.xpath('//div[@class="mapContainer"]/@data-lng')[0]
                lat = root.xpath('//div[@class="mapContainer"]/@data-lat')[0]
                map_info = str(lng) + ',' + str(lat)
            except:
                map_info = ''

        if not map_info:
            try:
                map_temp = re.compile(r'staticmap\?location=(.*?)&zoom').findall(content)[0]
                map_info = map_temp
            except:
                try:
                    map_temp = re.compile(r'&center=(.*?)&maptype').findall(content)[0]
                    map_infos = map_temp.split(',')
                    map_info = map_infos[1] + ',' + map_infos[0]
                except:
                    try:
                        map_temp = re.compile(r'desktop&center=(.*?)&zoom', re.S).findall(content)[0]
                        map_infos = map_temp.split(',')
                        map_info = map_infos[1] + ',' + map_infos[0]
                    except:
                        map_temp = ''
        if not map_info:
            map_info = ''
    except Exception as e:
        map_info = ''
        print 'map_info error', url
        print str(e)
        return "Error"
    print 'map: %s' % map_info

    # 地址address
    try:
        address = ''
        address = root.find_class('format_address')[0].text_content().strip().encode('utf-8').replace('地址: ', '')
    except Exception, e:
        address = ''
        # traceback.print_exc(e)
    print 'address: %s' % address

    # 电话tel
    try:
        tel = root.find_class('phoneNumber')[0].text
    except:
        tel = ''
    print 'tel: %s' % tel

    # 排名rank
    try:
        rank = ''
        rank_text = root.find_class('slim_ranking')[0].text_content().encode('utf-8').replace(',', '')
        nums = re.compile(r'(\d+)', re.S).findall(rank_text)
        # rank = nums[0] + '/' + nums[1]
        rank = nums[1]
    except Exception, e:
        rank = ''
    print 'rank: %s' % rank

    # 评分rating
    try:
        if len(root.find_class('rs rating')) != 0:
            grade_temp = root.find_class('rs rating')[0]
            rating = float(grade_temp.xpath('span/img/@content')[0])
            reviews = int(grade_temp.xpath('a/@content')[0])
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
    try:
        tagid = ''
        tagid = root.find_class('heading_details')[0].text_content().strip().encode('utf-8').split('\n')[-1].replace(
            ',', '|')
    except Exception, e:
        tagid = ''
    print 'tagid: %s' % tagid

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
        desc = ''
    print 'desc: %s' % desc

    # 卓越奖
    prize = 0
    try:
        test = root.find_class('taLnk text')
        if len(test) > 0:
            prize = 1
    except:
        pass

    # 旅行家标志
    traveler_choice = 0
    try:
        test = root.find_class('tchAward')
        if len(test) > 0:
            traveler_choice = 1
    except:
        pass

    # 图片抓取
    try:
        image_urls = image_paser(content, url)
    except:
        image_urls = ''

    # 第一条评论的review id 用于没有介绍时使用
    try:
        raw_onclick = root.find_class('reviewSelector')[1].xpath('./@id')[0]
        first_review_id = re.findall('review_(\d+)', raw_onclick)[0]
    except:
        first_review_id = ''

    print "source_city_id: ", source_city_id
    print "url: ", url

    encode_string = get_site_encode_string(content)

    print "encode_string: ", encode_string

    raw_site = ''
    if encode_string != '':
        raw_site = decode_raw_site(encode_string)

    print "raw_site: ", raw_site

    result = (
        source, name, name_en, tel, map_info, address, open_time, rating, rank, tagid, reviews, recommended_time, desc,
        prize, traveler_choice, first_review_id, image_urls,
        miaoji_id, source_id, source_city_id, url, encode_string, raw_site)
    return result


def insert_db(result, city_id):
    sql = "insert into tp_attr_basic_0213 (`source`, `name`, `name_en`, `phone`, `map_info`, `address`, `opentime`, `star`, `ranking`, `tagid`, `commentcounts`, `recommended_time`, `introduction`, `prize`, `traveler_choice`, `first_review_id`, `imgurl`,`miaoji_id`, `id`, `source_city_id`, `url`, `site_raw`, `site_before_301`, `city_id`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    result = list(result)
    result.append(city_id)
    return db.ExecuteSQL(sql, tuple(result))
