# coding=utf8
import json
import re

import db_localhost
from lxml import html
from pyquery import PyQuery

from proj.my_lib.Common.Browser import MySession
from proj.my_lib.Common.Utils import try3times
from decode_raw_site import decode_raw_site

img_get_url = 'http://www.tripadvisor.cn/LocationPhotoAlbum?detail='
introduction_url = 'https://www.tripadvisor.cn/MetaPlacementAjax?detail=%s&placementName=hr_btf_north_star_about&servletClass=com.TripResearch.servlet.accommodation.AccommodationDetail&servletName=Hotel_Review&more_content_request=true'

pattern_g = re.compile('-g(\d+)')

pattern = re.compile('\{\'aHref\'\:\'([\s\S]+?)\'\,\ \'')

pattern_d = re.compile('-d(\d+)')

ss = MySession(need_proxies=True)


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

@try3times(try_again_times=20)
def image_paser(detail_id):
    page = ss.get(img_get_url + detail_id)
    root = PyQuery(page.text)
    images_list = []
    for div in root('.photos.inHeroList div').items():
        images_list.append(div.attr['data-bigurl'])
    img_list = '|'.join(images_list)
    assert img_list != '', 'NO IMAGES'

    return img_list

@try3times(try_again_times=20)
def intro_parse(detail_id):
    page = ss.get(introduction_url % detail_id)
    root = PyQuery(page.text)
    return root('.description .section_content').text()

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
            # m@add meta 节点查找
            try:
                location_content = root.xpath('//meta[@name="location"]/@content')[0].strip()
                map_info = re.search('coord[=\s]+([\.\d\,\-]+)', location_content).group(1)
            except:
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
        tel = root.find_class('blEntry phone')[0][1].text
    except:
        tel = ''
    print 'tel: %s' % tel

    # 排名rank
    try:
        rank = ''
        rank_text = root.find_class('header_popularity popIndexValidation')[0].text_content().encode('utf-8').replace(',', '')
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
            rating = float(grade_temp.xpath('div/span/@content')[0])
            reviews = int(grade_temp.xpath('a/span')[0].text)
        else:
            rating = -1
            reviews = -1
    except Exception, e:
        # traceback.print_exc(e)
        rating = -1
        reviews = -1
    print 'rating: %s' % rating
    print 'reviews: %s' % reviews

    # 菜式 cuisines
    # 开店时间 open_time
    # 价格 price
    try:
        cuisines = ''
        table_section = root.find_class('table_section')[0]
        open_time = ''
        price = ''
        for ele in table_section[1:]:
            if ele.xpath('div')[0].text.find('菜系')>-1:
                cuisines = ele.xpath('div/a')[0].text
            if ele.xpath('div')[0].text.find('参考价位')>-1:
                price = ele.xpath('div/span')[0].text.replace('\n', ' ')
            if ele.xpath('div')[0].text.find('营业时间')>-1:
                opentime_detail = ele.xpath('.//div')[1]
                for ele_d in opentime_detail.xpath('div'):
                    open_week = ele_d.xpath('span')[0].text + '  '
                    time_ = ''
                    for ele_t in ele_d.xpath('span//div'):
                        time_ += ele_t.text + ' | '
                    open_time += open_week + time_[:-3] + '\n'
        open_time = open_time[:-1]
    except Exception, e:
        cuisines = ''
        open_time = ''
        price = ''
    # if cuisines.find('+新增菜系') > -1:
    #     cuisines = ''
    print 'cuisines: %s' % cuisines
    print 'open_time: %s' % open_time
    print 'price: ', price

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
        prize_ele = root.find_class('award award-coe ui_column is-6')
        if prize_ele:
            if prize_ele[0].xpath('div/span')[0].text.find('卓越奖')>-1:
                prize = 1
    except Exception, e:
        prize = 0

    print "Prize: ", prize

    # 旅行家标志
    traveler_choice = 0
    try:
        test = root.find_class('ui_icon travelers-choice-badge')
        if len(test) > 0:
            traveler_choice = 1
    except:
        pass

    print "Traveler choice: ", traveler_choice

    # 图片抓取
    image_urls = ''
    try:
        image_urls = image_paser(re.search(pattern_d, url).groups()[0])
    except Exception, e:
        image_urls = ''

    print 'Image_urls: ', image_urls

    if image_urls=='':
        raise Exception('NO IMAGES')

    # 简介抓取
    desc = ''
    try:
        desc = intro_parse(re.search(pattern_d, url).groups()[0])
    except Exception, e:
        desc = ''

    print 'desc: ', desc

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
    db_localhost.insert('rest', **result)


if __name__ == '__main__':
    import requests

    # url = 'https://www.tripadvisor.cn/Restaurant_Review-g187147-d9806534-Reviews-ASPIC-Paris_Ile_de_France.html'
    url = 'http://www.tripadvisor.cn/Restaurant_Review-g298490-d10001137-Reviews-Mimino-Blagoveshchensk_Amur_Oblast_Far_Eastern_District.html'
    page = requests.get(url)
    result = parse(page.content, url, 'NULL')
    # insert_db(result, 'NULL')
