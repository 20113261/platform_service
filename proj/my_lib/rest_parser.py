# coding=utf8
import json
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

import re, json
import traceback
import db_localhost
from urlparse import urljoin
from lxml import html
from pyquery import PyQuery

from proj.my_lib.Common.Browser import MySession
from proj.my_lib.Common.Utils import try3times
from decode_raw_site import decode_raw_site
from proj.my_lib.logger import get_logger
from proj.my_lib.Common.Utils import has_chinese

logger = get_logger('ImgList')

img_get_url = 'http://www.tripadvisor.cn/LocationPhotoAlbum?detail='
introduction_url = 'https://www.tripadvisor.cn/MetaPlacementAjax?detail=%s&placementName=hr_btf_north_star_about&servletClass=com.TripResearch.servlet.accommodation.AccommodationDetail&servletName=Hotel_Review&more_content_request=true'

pattern_g = re.compile('-g(\d+)')

pattern = re.compile('\{\'aHref\'\:\'([\s\S]+?)\'\,\ \'')

pattern_d = re.compile('-d(\d+)')


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


@try3times(try_again_times=10)
def image_parser(detail_id):
    with MySession(need_proxies=True, need_cache=True) as session:
        page = session.get(img_get_url + str(detail_id))
        root = PyQuery(page.text)
        images_list = []
        for div in root('.photos.inHeroList div').items():
            images_list.append(div.attr['data-bigurl'])
        img_list = '|'.join(images_list)
        assert img_list != '' or img_list is not None, 'NO IMAGES'
        logger.info('----0---------      ' + img_list)
        return img_list


@try3times(try_again_times=10)
def intro_parse(detail_id):
    with MySession(need_proxies=True, need_cache=True) as session:
        page = session.get(introduction_url % detail_id)
        root = PyQuery(page.text)
        return root('.description .section_content').text()


def parse(content, url, city_id, debug=False):
    rest_info = []
    try:
        content = content.decode('utf-8')
    except:
        return "Error"
    root = html.fromstring(content)

    # id等信息,source_id, source_city_id, soruce
    source_id = re.compile(r'd(\d+)').findall(url)[0]
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

    source = 'daodao'

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

    print('name: %s' % name)
    print('name_en: %s' % name_en)

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
        tel = root.find_class('blEntry phone')[0][1].text
        if not re.search(r'[0-9]+', tel):
            tel = ''
    except:
        tel = ''
    print 'tel: %s' % tel

    # 排名rank
    try:
        rank = ''
        rank_text = root.find_class('header_popularity popIndexValidation')[-1].text_content().encode('utf-8').replace(
            ',', '')
        nums = re.compile(r'(\d+)', re.S).findall(rank_text)
        # orank = nums[0] + '/' + nums[1]
        rank = nums[-1]
    except Exception, e:
        # traceback.print_exc(e)
        rank = '2000000'
    print 'rank: %s' % rank

    # 评分rating
    try:
        rating = -1
        reviews = -1
        if len(root.find_class('rs rating')) != 0:
            grade_temp = root.find_class('rs rating')[0]
            rating = float(grade_temp.xpath('div/span/@content')[0])
            reviews = int(re.search('\d+', grade_temp.text_content().replace(',', '')).group())
    except Exception, e:
        pass
    print 'rating: %s' % rating
    print 'reviews: %s' % reviews

    # 菜式 cuisines
    # 开店时间 open_time
    # 价格 price
    try:
        cuisines = ''
        table_section = root.xpath('//*[@class="table_section"]/*[@class="row"]')

        open_time = ''
        price = ''
        for ele in table_section[1:]:
            try:
                tab_title = ele.xpath('div[contains(@class, "title")]')[0].text
                tab_content = ele.xpath('div[contains(@class, "content")]')[0].text_content().replace('\n', ' ').strip()
                if tab_title.find('菜系') > -1:
                    cuisines = tab_content
                if tab_title.find('参考价位') > -1:
                    price = tab_content
                if tab_title.find('营业时间') > -1:
                    opentime_detail = ele.xpath('.//div')[1]
                    for ele_d in opentime_detail.xpath('div'):
                        open_week = ele_d.xpath('span')[0].text + '  '
                        time_ = ''
                        for ele_t in ele_d.xpath('span//div'):
                            time_ += ele_t.text + ' | '
                        open_time += open_week + time_[:-3] + '\n'
            except:
                print traceback.format_exc()
                pass
        open_time = open_time[:-1]
    except Exception, e:
        print traceback.format_exc()
        cuisines = ''
        open_time = ''
        price = ''
    # if cuisines.find('+新增菜系') > -1:
    #     cuisines = ''
    print 'cuisines: %s' % cuisines
    print 'open_time: %s' % open_time
    print 'price: ', price

    tagid = ''
    try:
        tagid = root.find_class('header_detail attraction_details')[0] \
            .xpath('div')[0].text_content().strip().encode('utf-8').split('\n')[-1].replace(',', '|')
    except Exception, e:
        tagid = ''

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
        # price = ''
        feature = ''
        dining_options = ''
        infos = root.find_class('details_tab')[0].find_class('table_section')[0].find_class('row')
        rows = []
        for info in infos:
            row = info.text_content().encode('utf-8').strip()
            # if row.find('价格') > -1:
            #     price = info.find_class('.ui_columns')[0].xpath('span/span').text_content().encode('utf-8').strip().replace('\n', '')
            if row.find('用餐选择') > -1:
                dining_options = info.find_class('content')[0].text_content().encode('utf-8').strip().replace('\n', '')
            if row.find('氛围类别') > -1:
                feature = info.find_class('content')[0].text_content().encode('utf-8').strip().replace('|', '')

    except Exception, e:
        print str(e)
        # price = ''
        feature = ''
        dining_options = ''

    # print 'price:', price
    print 'feature:', feature
    print 'dining_options:', dining_options
    menu = ''
    service = ''
    payment = ''

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
        except Exception as e:
            image_urls = ''

        print'Image_urls: ', image_urls
    else:
        image_urls = ''

    logger.info('----2---------      ' + image_urls)
    # 简介抓取
    desc = ''
    try:
        desc = root.xpath('//*[@id="OVERLAY_CONTENTS"]')[0].text_content().encode('utf-8').strip()
    except:
        try:
            desc = root.xpath('//*[@class="description"]/*[@class="text"]')[0].text_content().encode('utf-8').strip()
        except:
            desc = ''
    print 'desc: %s' % desc

    # 第一条评论的review id 用于没有介绍时使用
    try:
        raw_onclick = root.find_class('reviewSelector')[1].xpath('./@id')[0]
        first_review_id = re.findall('review_(\d+)', raw_onclick)[0]
    except:
        first_review_id = ''

    print "First review Id: ", first_review_id

    # 新添字段价格等级
    try:
        price_level = ''
        price_level_ele = root.find_class('ui_column is-6 price')
        if price_level_ele:
            price_level = price_level_ele[0].xpath('span')[0].text
    except Exception, e:
        price_level = ''

    print 'Price level: ', price_level

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
    except Exception as exc:
        dining_options = ''

    site = ''
    try:
        site_data = root.find_class('blEntry website')[0].attrib['data-ahref']
        site = decode_raw_site(site_data)
    except Exception, e:
        print(e)

    result = {
        'source': source,
        'name': name,  #
        'name_en': name_en,  #
        'phone': tel,  #
        'map_info': map_info,  #
        'address': address,
        'opentime': open_time,  #
        'grade': rating,
        'ranking': rank,
        # 'tagid': tagid,
        'cuisines': cuisines,
        'dining_options': dining_options,
        'menu': menu,
        'price': price,
        'price_level': price_level,
        'payment': payment,
        'service': service,
        'commentcounts': reviews,
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


# def insert_comment_page(args):
#     sql = 'insert into tp_rest_paging_0801 (`url`,`source_id`,`source_city_id`,`page_num`) VALUES (%s,%s,%s,%s)'
#     return db.ExecuteSQLs(sql, args)

# def insert_db(args):
#     sql = "INSERT INTO " + TASK_TABLE + " (`name`,`telphone`,`map_info`,`address`,`open_time`,`grade`,`real_ranking`,`cuisines`,`dining_options`,`review_num`,`rating_by_category`,`menu`,`price`,`description`,`service`,`payment`,`prize`,`traveler_choice`,`image_urls`,`id`,`res_url`,`first_review_id`,`price_level`,`source_city_id`,`site_raw`, `city_id`, `source`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'daodao')"
#     return db.ExecuteSQL(sql, args)

def insert_db(result, city_id):
    result['city_id'] = city_id
    if not result['imgurl']:
        raise Exception('zhao bu dao tupian')
    db_localhost.insert('rest', **result)


if __name__ == '__main__':
    import requests

    # url = 'https://www.tripadvisor.cn/Restaurant_Review-g187147-d9806534-Reviews-ASPIC-Paris_Ile_de_France.html'
    url = 'http://www.tripadvisor.cn/Restaurant_Review-g298490-d10001137-Reviews-Mimino-Blagoveshchensk_Amur_Oblast_Far_Eastern_District.html'
    url = 'https://www.tripadvisor.cn/Restaurant_Review-g187147-d9806534-Reviews-ASPIC-Paris_Ile_de_France.html'
    url = 'https://www.tripadvisor.cn/Restaurant_Review-g297930-d2704861-Reviews-The_Coffee_Club_Jungceylon-Patong_Kathu_Phuket.html'
    page = requests.get(url)
    result = parse(page.content, url, 'NULL')
    print json.dumps(result, ensure_ascii=False)
    # insert_db(result, 'NULL')
