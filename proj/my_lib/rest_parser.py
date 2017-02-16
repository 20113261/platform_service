# coding=utf8
import json
import re

import db_localhost as db
from lxml import html

pattern_g = re.compile('-g(\d+)')

pattern = re.compile('\{\'aHref\'\:\'([\s\S]+?)\'\,\ \'')

pattern_d = re.compile('-d(\d+)')
TASK_TABLE = "tp_rest_basic"


def dining_options_parser(content, url):
    root = html.fromstring(content)
    try:
        infos = root.find_class('details_tab')[0].find_class('table_section')[0].find_class('row')
        rows = []
        for info in infos:
            row = info.text_content().encode('utf-8').strip().replace('\n', '')
            rows.append(row.strip())

    except Exception, e:
        print str(e)
        rows = []

    return '|_|'.join(rows)


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


def parse(content, url, city_id):
    print 'url: %s' % url
    rest_info = []
    try:
        content = content.decode('utf-8')
    except:
        return "Error"
    root = html.fromstring(content)

    # id等信息,source_id, source_city_id, soruce
    source_id = re.compile(r'd(\d+)').findall(url)[0]
    # source_id = rest_id

    source = 'daodao'

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

    print 'name: %s' % name
    print 'name_en: %s' % name_en

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
    except Exception, e:
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
        # orank = nums[0] + '/' + nums[1]
        rank = nums[1]
    except Exception, e:
        # traceback.print_exc(e)
        rank = '2000000'
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
            time += ' '
            time += hours[n]
            if (n != len(days) - 1):
                time += '|'
        if time != '':
            open_time = time
        else:
            open_time = ''

            # if len( root.find_class('hoursOverlay') ) != 0 :
            #    open_time = root.find_class('hoursOverlay')[0].text_content().encode('utf-8')
    except Exception, e:
        # traceback.print_exc(e)
        open_time = ''
    print 'open_time: %s' % open_time

    # 菜式 cuisines
    try:
        cuisines = ''
        cuisines = root.find_class('heading_details')[0].text_content().strip().encode('utf-8').split('\n')[-1].replace(
            ', 更多', '').replace(',', '|')
    except Exception, e:
        cuisines = ''
    if cuisines.find('+新增菜系') > -1:
        cuisines = ''
    print 'cuisines: %s' % cuisines

    # 评级 rating_by_category
    try:
        temp = []
        for row in root.find_class("ratingRow wrap"):
            try:
                label = row.xpath('div[1]/span/text()')[0].encode('utf-8')
                score_tmp = re.compile(r's(\d+)').findall(row.xpath('div[2]/span/img/@class')[0])[0]
                score = ".".join(score_tmp)
                temp.append(label + ":" + score)
            except Exception, e:
                continue
        if temp != []:
            rating_by_category = '|'.join(temp)
        else:
            rating_by_category = ''
    except Exception, e:
        # traceback.print_exc(e)
        rating_by_category = ''
    print 'rating_by_category: %s' % rating_by_category

    # 用餐选择 dining_options
    # 价格 price
    # 氛围类别 feature
    try:
        price = ''
        feature = ''
        dining_options = ''
        infos = root.find_class('details_tab')[0].find_class('table_section')[0].find_class('row')
        rows = []
        for info in infos:
            row = info.text_content().encode('utf-8').strip()
            if row.find('价格') > -1:
                price = info.find_class('content')[0].text_content().encode('utf-8').strip().replace('\n', '')
            if row.find('用餐选择') > -1:
                dining_options = info.find_class('content')[0].text_content().encode('utf-8').strip().replace('\n', '')
            if row.find('氛围类别') > -1:
                feature = info.find_class('content')[0].text_content().encode('utf-8').strip().replace('|', '')

    except Exception, e:
        print str(e)
        price = ''
        feature = ''
        dining_options = ''

    print 'price:', price
    print 'feature:', feature
    print 'dining_options:', dining_options
    desc = ''
    menu = ''
    service = ''
    payment = ''

    # 卓越奖
    prize = 0
    try:
        test = root.find_class('taLnk text')
        if len(test) > 0:
            prize = 1
    except:
        pass

    print "Prize: ", prize

    # 旅行家标志
    traveler_choice = 0
    try:
        test = root.find_class('tchAward')
        if len(test) > 0:
            traveler_choice = 1
    except:
        pass

    print "Traveler choice: ", traveler_choice

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

    print "First review Id: ", first_review_id

    # 新添字段价格等级
    try:
        price_level = root.find_class('price_rating')[0].xpath('./text()')[0].strip()
    except:
        price_level = ''

    print 'Price level', price_level

    try:
        source_city_id = pattern_g.findall(url)[0]
    except:
        source_city_id = ''

    # 获取EncodeString

    try:
        encode_string = get_site_encode_string(content)
    except:
        encode_string = ''

    # # 添加评论页
    # try:
    #     comment_data_list = get_review_page(content, url)
    # except:
    #     comment_data_list = []
    #
    # if len(comment_data_list) != 0:
    #     insert_comment_page(comment_data_list)
    try:
        dining_options = dining_options_parser(content, url)
    except:
        dining_options = ''

    rest_info = (
        name, tel, map_info, address, open_time, rating, rank, cuisines, dining_options, reviews, rating_by_category,
        menu,
        price, desc, service, payment, prize, traveler_choice, image_urls, source_id, url, first_review_id, price_level,
        source_city_id, encode_string, city_id)
    insert_db(rest_info)
    return rest_info


# def insert_comment_page(args):
#     sql = 'insert into tp_rest_paging_0801 (`url`,`source_id`,`source_city_id`,`page_num`) VALUES (%s,%s,%s,%s)'
#     return db.ExecuteSQLs(sql, args)

def insert_db(args):
    sql = "INSERT INTO " + TASK_TABLE + " (`name`,`telphone`,`map_info`,`address`,`open_time`,`grade`,`real_ranking`,`cuisines`,`dining_options`,`review_num`,`rating_by_category`,`menu`,`price`,`description`,`service`,`payment`,`prize`,`traveler_choice`,`image_urls`,`id`,`res_url`,`first_review_id`,`price_level`,`source_city_id`,`site_raw`, `city_id`, `source`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'daodao')"
    return db.ExecuteSQL(sql, args)
