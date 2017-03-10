# coding=utf-8
# coding='utf8'
import re

from proj.tasks import get_comment


def add_target(task_url, miaoji_id, **kwargs):
    res1 = get_comment.delay(task_url, 'zhCN', miaoji_id, **kwargs)
    res2 = get_comment.delay(task_url, 'en', miaoji_id, **kwargs)
    return res1, res2


d_pattern = re.compile('-d(\d+)')

if __name__ == '__main__':
    # import random
    # import time
    # from proj.tasks import add
    #
    # task_list = []
    # for i in range(10):
    #     task_list.append(add.delay(random.randint(1, 100), random.randint(1, 100)))
    #
    # while not all(map(lambda x: x.ready(), task_list)):
    #     time.sleep(1)
    #     print 'wait 1 second'
    #
    # for each in task_list:
    #     print each.get()

    #  todo get_comment attr
    # from get_url.get_comment_url import get_attr_url
    # from get_url.get_finish_comment_review_from_url import get_finish_source_id
    #
    # finish_source_id = get_finish_source_id()
    # for url, miaoji_id in get_attr_url():
    #     if d_pattern.findall(url)[0] not in finish_source_id:
    #         add_target(url, miaoji_id)

    # todo get_comment shop

    # from get_url.get_comment_url import get_shop_url
    #
    # for url, miaoji_id in get_shop_url():
    #     add_target(url, miaoji_id)
    #
    # # todo get_comment rest
    # from get_url.get_comment_url import get_rest_url
    #
    # for url, miaoji_id in list(get_rest_url()):
    #     add_target(url, miaoji_id)
    # for url in open('/tmp/url'):
    #     get_.delay(url.strip())

    # todo get_comment total NEW
    # from random import shuffle
    # from get_url.get_comment_url import get_total
    #
    # _url_set = set()
    # for url, miaoji_id in list(get_total()):
    #     # add_target(url, miaoji_id)
    #     _url_set.add(url)
    #
    # _url_list = list(_url_set)
    # shuffle(_url_list)
    # for url in _url_list[:5]:
    #     print url
    # # print url

    # todo get_comment attr
    # from get_url.get_comment_url import get_attr_url
    #
    # for url, miaoji_id in list(get_attr_url()):
    #     add_target(url, miaoji_id)
    #     print url

    # todo get_comment NEW With Task
    # _count = 0
    # for task_id, args in get_task(worker='poi_comment'):
    #     add_target(args['url'], args['mid'], task_id=task_id)
    #     _count += 1
    # print _count
    # todo get_long_comment NEW
    # from get_url.get_long_comment_url import get_task
    # from proj.tasks import get_long_comment
    #
    # _count = 0
    # for url, language, miaoji_id in get_task():
    #     _count += 1
    #     if _count == 60000:
    #         break
    #     get_long_comment.delay(url, language, miaoji_id)
    # print _count

    # todo get_lost_attr
    # from proj.tasks import get_lost_attr
    #
    # url_file = open('/tmp/url_file')
    # for url in url_file:
    #     get_lost_attr.delay(url.strip())
    #
    # from proj.tasks import get_lost_attr
    # from additions.get_new_url import new_attr_url
    # for url in new_attr_url():
    #     get_lost_attr.delay(url.strip())
    #
    # from proj.tasks import get_lost_attr
    # from additions.get_total_url import get_attr_set
    # for url in get_attr_set():
    #     get_lost_attr.delay(url.strip())
    #     print url

    # from proj.tasks import get_lost_attr
    # from read_detail_url.get_url import get_url
    # for url in get_url('attr'):
    #     # get_lost_attr.delay(url.strip())
    #     get_lost_attr.delay('http://www.tripadvisor.cn/Attraction_Review-g1761683-d155619-Reviews-Emerald_Lake-Yoho_National_Park_Kootenay_Rockies_British_Columbia.html')
    #     print url

    # todo get_site
    # import db_localhost as db
    # from proj.tasks import get_site_url
    #
    # # table_name = 'tp_attr_basic_0213'
    # table_name = 'tp_shop_basic_0213'
    # sql = 'select id,site_before_301 from {0} where site is null and site_before_301!=""'.format(table_name)
    # for each in db.QueryBySQL(sql):
    #     source_id = each['id']
    #     site_before_301 = each['site_before_301']
    #     get_site_url.delay(site_before_301, source_id, table_name)


    # todo get_lost_rest
    # from proj.tasks import get_lost_rest
    #
    # # url_file = open('/tmp/rest_url_file')
    # # for url in url_file:
    # #     get_lost_rest.delay(url.strip())
    #
    # for url in open('/tmp/url'):
    #     get_lost_rest.delay(url.strip())
    # from proj.tasks import get_lost_rest
    # from additions.get_new_url import new_rest_url
    #
    # for url in new_rest_url():
    #     get_lost_rest.delay(url.strip())

    # from proj.tasks import get_lost_rest
    # from read_detail_url.get_url import get_url
    # for url in get_url('rest'):
    #     get_lost_rest.delay(url.strip())
    #     print url


    # todo get_lost_shop
    # from proj.tasks import get_lost_shop
    #
    # url_file = open('/tmp/shop_url_file')
    # for url in url_file:
    #     get_lost_shop.delay(url.strip())
    # from proj.tasks import get_lost_shop
    # from additions.get_new_url import new_shop_url
    #
    # for url in new_shop_url():
    #     get_lost_shop.delay(url.strip())

    # from proj.tasks import get_lost_shop
    # from additions.get_total_url import get_shop_set
    #
    # for url in get_shop_set():
    #     get_lost_shop.delay(url.strip())
    #     print url

    # url_l = ["http://www.tripadvisor.cn/Attraction_Review-g1074321-d10833005-Reviews-Andonggu_Sijang_Sanginhoe-Andong_Gyeongsangbuk_do.html","http://www.tripadvisor.cn/Attraction_Review-g1074321-d10833005-Reviews-Andonggu_Sijang_Sanginhoe-Andong_Gyeongsangbuk_do.html"]
    # from proj.tasks import get_lost_shop
    #
    # for url in url_l:
    #     get_lost_shop.delay(url.strip())
    # count = 0
    # url_set = set()
    # from proj.tasks import get_lost_shop
    # from read_detail_url.get_url import get_url
    #
    # for url in get_url('shop'):
    #     get_lost_shop.delay(url.strip())
    # print count


    # todo get_lost_rest_new
    # from proj.tasks import get_lost_rest_new
    # #
    # # for line in db.QueryBySQL('select res_url from tp_rest_basic_0801 limit 500000'):
    # #     res_url = line['res_url']
    # #     get_lost_rest_new.delay(res_url)
    # for url in open('/tmp/url'):
    #     get_lost_rest_new.delay(url.strip())

    # todo get_lost_attr_no_proxy
    # # from proj.tasks import get_lost_rest_no_proxy
    # #
    # # url_file = open('/tmp/url')
    # # for url in url_file:
    # #     get_lost_rest_no_proxy.delay(url.strip())
    #
    # # todo get_img
    # import hashlib
    # import os
    # from proj.tasks import get_images_without_proxy
    #
    # # url_list_file = ['pic_task_2016_10_07_21', 'pic_task_2016_10_07_22', 'pic_task_2016_10_07_23',
    # #                  'pic_task_2016_10_07_24',
    # #                  'pic_task_2016_10_07_25', 'pic_task_2016_10_07_26', 'pic_task_2016_10_07_27',
    # #                  'pic_task_2016_10_07_28']
    # # url_list_file = ['attr_url_list', 'rest_url_list', 'shop_url_list']
    # # url_list_file = ['attr_url_list', 'shop_url_list']
    # # url_list_file = ['img_url_1101', 'img_url_1103', 'img_url_test']
    # # url_list_file = ['img_url_1130_rest','img_url_1130_shop','img_url_1130_attr']
    # # url_list_file = ['img_url_1130_attr','img_url_1130_shop']
    # # url_list_file = ['img_url_1130_attr']
    # # url_list_file = ['pic_task_2016_12_13_1', 'pic_task_2016_12_13_2', 'pic_task_2016_12_13_4',
    # # 'pic_task_2016_12_13_5', 'pic_task_2016_12_13_6']
    # # url_list_file = ['test_123123']
    # # url_list_file = ['booking_pic_task_2016_12_15_4part','ctrip_pic_task_2016_12_15_4part','expedia_pic_task_2016_12_15_4part','venere_pic_task_2016_12_15_4part']
    # url_list_file = ['attr_img_url_2017_01_04_12', 'rest_img_url_2017_01_04_12', 'shop_img_url_2017_01_04_12']
    # url_list_file.reverse()
    # count = 0
    # break_flag = False
    # for file_name in url_list_file:
    #     path = '/search/image/' + file_name + '_celery'
    #     if os.path.exists(path):
    #         already_downloaded = set(os.listdir(path))
    #     else:
    #         already_downloaded = set([])
    #     for url in open('/tmp/' + file_name):
    #         if hashlib.md5(url.strip()).hexdigest() + '.jpg' not in already_downloaded:
    #             get_images_without_proxy.delay(file_name + '_celery', url.strip())
    #             # print url.strip()
    #             count += 1
    #             if count == 100000:
    #                 break_flag = True
    #                 break
    #     if break_flag:
    #         break
    # print count
    # todo get_img_without_md5
    # from proj.tasks import get_images_without_md5
    # from handle_image.get_image import online,offline,get_id_img
    # for mid,img in get_id_img(online):
    #     get_images_without_md5.delay('attr_img_1010_celery', 'http://mioji-attr.kssws.ks-cdn.com/'+img)
    # for mid, img in get_id_img(offline):
    #     get_images_without_md5.delay('attr_img_1010_celery', 'http://mioji-attr.kssws.ks-cdn.com/'+img)

    # from proj.tasks import get_images_without_md5
    # from get_image import get_task
    #
    # count = 0
    # for img_url in get_task():
    #     get_images_without_md5.delay('attr_all_img', img_url)
    #     count += 1
    # print count

    # from ks3.connection import Connection
    # from proj.tasks import get_images_without_md5
    # import os
    #
    # already_download = set(os.listdir('/search/image/city_img'))
    #
    # ak = 'K0fJOlnF++ck5LznhuNZ'
    # sk = 'o4D5wjs6r02dxLDLyLbTTUenTvpmKgrBItra6qgb'
    # c = Connection(ak, sk)
    # b = c.get_bucket('mioji-mobilepic')
    # name_list = [k.name for k in b.list()]
    # for name in name_list[1:]:
    #     if name not in already_download:
    #         get_images_without_md5.delay('city_img','http://mioji-mobilepic.kssws.ks-cdn.com/'+name)

    # todo get_img_without_md5_and_proxy
    # from proj.tasks import get_images_without_md5_and_proxy
    # from ks3.connection import Connection
    # import os
    # import sys
    #
    # reload(sys)
    # sys.setdefaultencoding('utf8')
    #
    # already_download = set([f_name.decode('utf8') for f_name in os.listdir('/search/image/city_img_2')])
    #
    # ak = 'K0fJOlnF++ck5LznhuNZ'
    # sk = 'o4D5wjs6r02dxLDLyLbTTUenTvpmKgrBItra6qgb'
    # c = Connection(ak, sk)
    # b = c.get_bucket('mioji-mobilepic')
    # name_list = [k.name for k in b.list()]
    # for name in name_list[1:]:
    #     if name not in already_download:
    #         print name
    #         get_images_without_md5_and_proxy.delay('city_img_2','http://mioji-mobilepic.kssws.ks-cdn.com/'+name.encode('utf8'))




    # todo expedia_comment
    # from proj.tasks import expedia_comment
    #
    # _count = 0
    # for url in open('/tmp/expedia_task_1209'):
    #     expedia_comment.delay(url.strip())
    #     _count+=1
    # print _count

    # todo venere_comment
    # from proj.tasks import venere_comment
    #
    # _count = 0
    # for url in open('/tmp/venere_task_1209'):
    #     venere_comment.delay(url.strip())
    #     _count+=1
    # print _count
    #
    # # todo booking_comment
    # from proj.tasks import booking_comment
    #
    # _count=0
    # for url in open('/tmp/booking_task_1209'):
    #     booking_comment.delay(url.strip())
    #     _count+=1
    # print _count

    # todo booking_without_proxy
    # from proj.tasks import booking_comment_without_proxy
    #
    # for url in open('/tmp/booking_task_0927'):
    #     booking_comment_without_proxy.delay(url.strip())

    # todo tourico_base_data

    # from proj.my_lib.tourico.func import get_task_new
    # from proj.tasks import tourico_base_data
    #
    # # for hotel_id, tri_code in get_task():
    # #     # print hotel_id, tri_code
    # #     tourico_base_data.delay(hotel_id, tri_code)
    #
    # for hotel_id in get_task_new():
    #     tourico_base_data.delay(hotel_id, '')

    # todo tourico_hotel_id
    # from proj.tasks import tourico_hotel_id
    #
    # f = open('/tmp/city_info.csv')
    # # f = open('/tmp/unfinished_city')
    # for line in f:
    #     continent_name, country_name, state_name, city_name = line.strip().split('###')
    #     tourico_hotel_id.delay(continent_name, country_name, state_name, city_name)

    # from proj.my_lib.tourico.func_2 import insert_total_city
    #
    # f = open('/tmp/city_info.csv')
    # for line in f:
    #     continent_name, country_name, state_name, city_name = line.strip().split('###')
    #     print insert_total_city((continent_name, country_name, state_name, city_name))

    # todo get_images_info
    # import os
    # import db_localhost
    # from proj.tasks import get_images_info
    #
    # #
    # # def get_already_calculated():
    # #     _set = set()
    # #     sql='select file_name from image_info'
    # #     for line in db_localhost.QueryBySQL(sql):
    # #         _set.add(line['file_name'].split('_')[0])
    # #     return _set
    # #
    # # already_calculated = get_already_calculated()
    # # # path_list = ['/search/image/pic_task_2016_12_13_1_celery/',
    # # #              '/search/image/pic_task_2016_12_13_2_celery/',
    # # #              '/search/image/pic_task_2016_12_13_3_celery/',
    # # #              '/search/image/pic_task_2016_12_13_4_celery/',
    # # #              '/search/image/pic_task_2016_12_13_5_celery/',
    # # #              '/search/image/pic_task_2016_12_13_6_celery/']
    # # # path = '/search/image/img_url_1130_rest_celery/'
    # # path_list = ['/search/image/attr_img_url_2017_01_04_12_celery/',
    # #              '/search/image/rest_img_url_2017_01_04_12_celery/',
    # #              '/search/image/shop_img_url_2017_01_04_12_celery/']
    # path_list = ['/search/image/attr_img_task_170217']
    # total = 0
    # for path in path_list:
    #     _count = 0
    #     for file_name in os.listdir(path):
    #         # if file_name not in already_calculated:
    #         get_images_info.delay(os.path.join(path, file_name))
    #         _count += 1
    #     print _count
    #     total += _count
    # print total

    # todo trip_advisor_comment
    # from proj.my_lib.poi_comment.get_task import get_task_full
    # from random import shuffle
    #
    # _task_set = set()
    #
    # for mid, url in get_task_full('attr'):
    #     _task_set.add((url, mid))
    # for mid, url in get_task_full('rest'):
    #     _task_set.add((url, mid))
    # for mid, url in get_task_full('shop'):
    #     _task_set.add((url, mid))
    #
    # task_list = list(_task_set)
    # del _task_set
    # shuffle(task_list)
    # _count = 0
    # for url, mid in task_list:
    #     add_target(url, mid)
    #     _count += 1
    #     if _count >= 50000:
    #         break


    # todo poi_img_recrawl
    # from proj.my_lib.poi_img.get_task import get_task_full
    # from proj.tasks import poi_images_list
    #
    # for mid, url in get_task_full('attr'):
    #     # poi_images_list_without_proxy.delay(url, mid)
    #     poi_images_list.delay(url, mid)

    # todo HOTEL IMAGE
    # # import os
    # # from proj.tasks import get_hotel_images_info
    # #
    # # # path1 = '/search/images/'
    # # # path_list1 = ['pic_task_2016_10_07_1', 'pic_task_2016_10_07_12', 'pic_task_2016_10_07_15', 'pic_task_2016_10_07_16',
    # # #               'pic_task_2016_10_07_17', 'pic_task_2016_10_07_18', 'pic_task_2016_10_07_19', 'pic_task_2016_10_07_2',
    # # #               'pic_task_2016_10_07_20', 'pic_task_2016_10_07_21', 'pic_task_2016_10_07_22', 'pic_task_2016_10_07_3',
    # # #               'pic_task_2016_10_07_4', 'pic_task_2016_10_07_5', 'pic_task_2016_10_07_6', 'pic_task_2016_10_07_7',
    # # #               'pic_task_2016_10_07_8', 'pic_task_2016_10_07_9']
    # #
    # # path2 = '/search/image/'
    # # # path_list2 = ['pic_task_2016_12_13_1_celery', 'pic_task_2016_12_13_2_celery', 'pic_task_2016_12_13_3_celery',
    # # #               'pic_task_2016_12_13_4_celery', 'pic_task_2016_12_13_5_celery', 'pic_task_2016_12_13_6_celery',]
    # # path_list2 = ['booking_pic_task_2016_12_15_4part_celery', 'ctrip_pic_task_2016_12_15_4part_celery',
    # #               'expedia_pic_task_2016_12_15_4part_celery', 'venere_pic_task_2016_12_15_4part_celery', ]
    # # # for s_path in path_list1:
    # # #     for file_name in os.listdir(path1 + s_path):
    # # #         path = path1 + s_path + '/' + file_name
    # # #         get_hotel_images_info.delay(path)
    # #
    # # for s_path in path_list2:
    # #     for file_name in os.listdir(path2 + s_path):
    # #         path = path2 + s_path + '/' + file_name
    # #         get_hotel_images_info.delay(path)
    # import os
    # from proj.tasks import get_hotel_images_info
    #
    # # path, part, desc_part
    # # src_path = '/data/image/hotelinfo_zls_lx20161226_img'
    # # for file_name in os.listdir(src_path):
    # #     path = os.path.join(src_path, file_name)
    # #     get_hotel_images_info.delay(path=path, part='24', desc_path='/data/image/hotel_img_0112_1')
    #
    # src_path = '/data/image/adding_img_0111_img_task'
    # for file_name in os.listdir(src_path):
    #     path = os.path.join(src_path, file_name)
    #     get_hotel_images_info.delay(path=path, part='25', desc_path='/data/image/hotel_img_0112_2')

    # todo upload_img
    # from proj.tasks import upload_img
    # import os
    # import db_localhost
    #
    #
    # def get_path_list():
    #     file_set = set()
    #     sql = 'select path from finish_path'
    #     for line in db_localhost.QueryBySQL(sql):
    #         file_set.add(line['path'])
    #     return file_set
    #
    #
    # # path = '/search/image/rest_result/'
    # already_upload = get_path_list()
    # path = '/search/image/pic_task_2016_10_07_10_celery/'
    # bucket_name = 'mioji-hotel'
    # for file_name in os.listdir(path):
    #     upload_img.delay(bucket_name, path + file_name)
    # # for file_name in os.listdir(path):
    # #     if file_name not in already_upload:
    # #         upload_img.delay(bucket_name, path + file_name)

    # todo qyer_img
    #
    # from proj.my_lib.qyer_img.qyer_img import get_task
    # from proj.tasks import qyer_img_task
    #
    # for mid, url in get_task():
    #     qyer_img_task.delay(url, mid)

    # todo switzerland_task

    # from proj.my_lib.switzerland.switzerland import get_task
    # from proj.tasks import switzerland_task
    #
    # count = 0
    # for target_url, m_id, m_type in get_task():
    #     switzerland_task.delay(target_url, m_id, m_type)
    #     count += 1
    #     print target_url
    # print count

    # todo yelp_price_level
    # from proj.my_lib.price_level.get_url import get_yelp_task
    # from proj.tasks import yelp_price_level
    #
    # for m_id, url in get_yelp_task():
    #     yelp_price_level.delay(url, m_id)

    # todo daodao_price_level
    # from proj.my_lib.price_level.get_url import get_daodao_task
    # from proj.tasks import daodao_price_level
    #
    # for m_id, url in get_daodao_task():
    #     daodao_price_level.delay(url, m_id)

    # todo get_lost_poi_image
    # import os
    # from proj.tasks import get_lost_poi_image
    #
    # # downloaded_img = set(os.listdir('/search/image/not_upload_celery'))
    # for line in open('/tmp/not_upload'):
    #     file_name, src_url = line.strip().split('###')
    #     # if file_name not in downloaded_img:
    #     get_lost_poi_image.delay('attr_not_upload_celery', file_name.strip().split('.jpg')[0], src_url.strip())

    # todo get_daodao_image
    # def get_daodao_image_url(self, source_url, mid):
    # from proj.tasks import get_daodao_image_url
    # import db_test
    # import db_114_35_shop
    # import db_114_35_attr
    # import db_114_35_rest
    # import json
    # import db_localhost
    #
    #
    # def get_already_mid():
    #     _set = set()
    #     sql = 'select mid from daodao_img'
    #     for line in db_localhost.QueryBySQL(sql):
    #         _set.add(line['mid'])
    #     return _set
    #
    #
    # already_set = get_already_mid()
    #
    # def get_task():
    #     sql = 'select id,url from chat_shopping'
    #     for line in db_114_35_shop.QueryBySQL(sql):
    #         if line['id'] in already_set:
    #             continue
    #         url_dict = json.loads(line['url'])
    #         if 'daodao' in url_dict.keys():
    #             yield line['id'], url_dict['daodao']
    #
    #
    # # def get_task():
    # #     sql = 'select id,res_url from chat_restaurant where source like "%daodao%" and city_id in ("10415","11534","11555","20045","10423","10426","11512","10427","10024","10059","10158","10242","10428","11529","11530","11531","11532","11552","11557","11560","10443","10109","10281","10300","11322","11527","11543","11548","10039","10110","10123","10133","10135","10140","10180","10192","10194","10408","10483","11123","11266","11517","11518","11541","11546","11553","11556","11564","10487","10494","10094","10147","10182","10199","10226","10249","10729","11338","11365","11537","11554","10141","10230","10075","10540","11535","11545","11550","11558","11561","11563","10055","10126","10152","10222","10315","10324","10541","11211","11549","11559","10549","10550","10551","10553","11528","10555","10556","11516","10561","11522","11523","11524","11525","11096","10186","10190","11544","10402","11070","10066","10080","10137","10155","10187","10272","10282","10303","10384","10388","11164","11413","11533","11536","11547","11562","11526","10598","10615","11488","11519","11520","11521","11542","10058","10060","10087","10129","10205","11429","10314","11300","11540","10067","10069","10125","10130","10150","10163","10183","10208","10210","10219","10221","10224","10263","10275","10356","10656","11106","11269","11513","11514","11515","11538","11539","10040","10044","10105","10139","10162","10232","10674","10680","10683","11010","11398","11405","11468","11551","20393")'
    # #     for line in db_114_35_rest.QueryBySQL(sql):
    # #         if line['id'] not in already_set:
    # #             yield line['id'], line['res_url']
    #
    # _count = 0
    # for mid, source_url in get_task():
    #     get_daodao_image_url.delay(source_url, mid)
    #     _count += 1
    # print _count

    # # todo craw_html
    # # test

    # from proj.tasks import craw_html
    #
    # craw_html('http://maps.google.cn/maps/api/directions/json?origin=0.462707,73.154697&destination=3.986676,72.721657&region=es&sensor=false&mode=driving&depature_time=1483916400&alternatives=true&a1=v247737&a2=v247984&cciittyy=20218','abc_test','new_crawled_html_3')

    # todo run
    # import os
    # import hashlib
    # import MySQLdb
    # from proj.tasks import craw_html

    # too large task running
    # per_table_count = 600000
    # per_queue_count = 100000
    #
    #
    # def get_md5(src):
    #     return hashlib.md5(src).hexdigest()
    #
    #
    # def get_line(_path):
    #     for file_name in os.listdir(_path):
    #         file_path = os.path.join(_path, file_name)
    #         f = open(file_path)
    #         for _line in f:
    #             yield _line.strip()
    #
    #
    # def get_already_crawled():
    #     _set = set()
    #     conn = MySQLdb.connect(host='10.10.231.105', user='hourong', passwd='hourong', db='crawled_html')
    #     with conn as cursor:
    #         sql = 'select md5 from crawled_html.new_crawled_html_3_total'
    #         cursor.execute(sql)
    #         for line in cursor.fetchall():
    #             _set.add(line[0])
    #     return _set
    #
    #
    # def get_table_count(table_name):
    #     conn = MySQLdb.connect(host='10.10.231.105', user='hourong', passwd='hourong', db='crawled_html')
    #     with conn as cursor:
    #         sql = 'select count(*) from crawled_html.{}'.format(table_name)
    #         cursor.execute(sql)
    #         for line in cursor.fetchall():
    #             return line[0]
    #
    #
    # # get now table name
    # # all_table_list = [
    # #    'new_crawled_html_0',
    # #    'new_crawled_html_1',
    # #    'new_crawled_html_2',
    # #    'new_crawled_html_3',
    # #    'new_crawled_html_4',
    # #    'new_crawled_html_5',
    # #    'new_crawled_html_6',
    # #    'new_crawled_html_7',
    # #    'new_crawled_html_8',
    # #    'new_crawled_html_9'
    # # ]
    #
    # # all_table_list = [
    # #      'new_crawled_html_1_0',
    # #      'new_crawled_html_1_1',
    # #      'new_crawled_html_1_2',
    # #      'new_crawled_html_1_3',
    # #      'new_crawled_html_1_4',
    # #      'new_crawled_html_1_5',
    # #      'new_crawled_html_1_6',
    # #      'new_crawled_html_1_7',
    # #      'new_crawled_html_1_8',
    # #      'new_crawled_html_1_9'
    # # ]
    # all_table_list = ['new_crawled_html_3_' + str(i) for i in range(30)]
    #
    # for t_name in all_table_list:
    #     if get_table_count(t_name) < (per_table_count - per_queue_count + int(0.2 * per_queue_count)):
    #         break
    # else:
    #     t_name = all_table_list[-1]
    #
    # table_name = t_name
    #
    # already_crawled = get_already_crawled()
    # _count = 0
    #
    # # too large google drive crawl
    # task_file = open('/root/data/task/traffic_total_last_new')
    # for line in task_file:
    #     task_url, flag = line.strip().split('|_||_|')
    #     if get_md5(task_url) not in already_crawled:
    #         craw_html.delay(task_url, flag, table_name)
    #         _count += 1
    #         if _count >= per_queue_count:
    #             break
    # print _count

    #
    # # todo add simple task
    # import MySQLdb
    # import hashlib
    #
    # flag = 'google_long_drive_url_0110'
    # crawled_table = 'crawled_html'
    #
    #
    # def get_already_crawled():
    #     _set = set()
    #     conn = MySQLdb.connect(host='10.10.231.105', user='hourong', passwd='hourong', db='crawled_html')
    #     with conn as cursor:
    #         sql = 'select md5 from crawled_html.{0}'.format(crawled_table)
    #         cursor.execute(sql)
    #         for line in cursor.fetchall():
    #             _set.add(line[0])
    #     return _set
    #
    # def get_md5(src):
    #     return hashlib.md5(src).hexdigest()
    #
    # already_crawled = get_already_crawled()
    # task_file = open('/tmp/'+flag)
    # _count = 0
    # for line in task_file:
    #     if get_md5(line.strip()) in already_crawled:
    #         craw_html.delay(line.strip(), flag, crawled_table)
    #         _count += 1
    # print _count

    # # todo tp_city_attr_crawl
    # from proj.tasks import tp_attr_city_page
    #
    # import csv
    #
    # _count = 0
    # f = open('/tmp/tp_1227.csv')
    # f.readline()
    # reader = csv.reader(f)
    # for line in reader:
    #     if line[4] != 'NULL':
    #         print line[0], line[4]
    #         _count += 1
    #
    #         # tp_attr_list_page_num.delay(line[-1],line[0])
    # print _count
    #
    # tp_attr_city_page.delay('http://www.tripadvisor.cn/Tourism-g187147-Paris_Ile_de_France-Vacations.html', '10001')

    # todo tp_city_rest_crawl
    # from proj.tasks import tp_rest_list_page_num
    #
    # import csv
    # _count = 0
    # f = open('/tmp/tp_1207.csv')
    # f.readline()
    # reader = csv.reader(f)
    # for line in reader:
    #     if line[-1]!='0':
    #         # tp_rest_city_page.delay('http://www.tripadvisor.cn/Tourism-g187147-Paris_Ile_de_France-Vacations.html', '10001')
    #         print line[0],line[-1]
    #         tp_rest_list_page_num.delay(line[-1],line[0])
    #         _count+=1
    # print _count
    #
    # todo tp_city_shop_crawl

    # from proj.tasks import tp_shop_city_page
    #
    # from proj.tasks import tp_shop_list_page_num
    # import csv
    #
    # _count = 0
    # f = open('/tmp/shop_1207.csv')
    # f.readline()
    # reader = csv.reader(f)
    # for line in reader:
    #     if line[-1] != '0' and line[0].isdigit():
    #         print line[0], line[-1]
    #         tp_shop_list_page_num.delay(line[-1],line[0])
    #         _count+=1
    #         # tp_shop_city_page.delay('http://www.tripadvisor.cn/Tourism-g187147-Paris_Ile_de_France-Vacations.html', '10001')
    #
    # print _count

    # todo tp_city_init
    #
    # from proj.tasks import tp_shop_city_page, tp_rest_city_page, tp_attr_city_page
    #
    # attr_target_set = ["11534", "11555", "10059", "11529", "11531", "11532", "11552", "11557", "11560", "11527",
    #                    "11543", "10039", "10408", "10483", "11266", "11518", "11541", "11546", "11556", "11564",
    #                    "10094", "10226", "11338", "11537", "11554", "10075", "11550", "11558", "11563", "11549",
    #                    "11559", "11524", "11525", "10186", "10190", "11544", "11070", "10137", "10155", "10187",
    #                    "10272", "10282", "10384", "10388", "11164", "11413", "11533", "11536", "11547", "11562",
    #                    "11488", "11519", "11542", "10314", "11300", "11540", "10208", "11269", "11513", "11514",
    #                    "11515", "11538", "11539", "10139", "11010", "11398", "11405", "11468", "11551", "20393"]
    # rest_target_set = ["11529", "11531", "11532", "11552", "11557", "11560", "11564", "10226", "11537", "11550",
    #                    "11561", "11563", "10152", "11559", "10186", "10190", "11544", "10137", "10282", "10388",
    #                    "11413", "11533", "11536", "11547", "11519", "11269", "11514", "11539", "11468"]
    # shop_target_set = ["10415", "11534", "11555", "11512", "10059", "10158", "10428", "11529", "11530", "11531",
    #                    "11532", "11552", "11557", "11560", "10281", "10300", "11322", "11527", "11543", "11548",
    #                    "10039", "10110", "10123", "10133", "10135", "10140", "10180", "10192", "10194", "10408",
    #                    "10483", "11123", "11266", "11517", "11518", "11541", "11546", "11556", "11564", "10094",
    #                    "10182", "10226", "10249", "10729", "11338", "11365", "11537", "11554", "10141", "10230",
    #                    "10075", "10540", "11535", "11545", "11550", "11558", "11561", "11563", "10055", "10126",
    #                    "10152", "10222", "10324", "10541", "11211", "11549", "11559", "10551", "10553", "10555",
    #                    "11516", "11522", "11523", "11524", "11525", "11096", "10186", "10190", "11544", "10402",
    #                    "11070", "10066", "10080", "10137", "10155", "10187", "10272", "10282", "10303", "10384",
    #                    "10388", "11164", "11413", "11533", "11536", "11547", "11562", "11526", "10615", "11488",
    #                    "11519", "11542", "10058", "10087", "10129", "10205", "11429", "10314", "11300", "11540",
    #                    "10067", "10069", "10130", "10150", "10183", "10210", "10221", "10224", "10263", "10275",
    #                    "10356", "11106", "11269", "11513", "11514", "11515", "11538", "11539", "10040", "10044",
    #                    "10105", "10139", "10162", "10680", "10683", "11010", "11398", "11405", "11468", "11551",
    #                    "20393"]
    # import csv
    #
    # _count = 0
    # f = open('/tmp/tp_1227.csv')
    # f.readline()
    # reader = csv.reader(f)
    # for line in reader:
    #     if line[4] != 'NULL':
    #         print line[0], line[4]
    #         # _count += 1
    #         # if line[0] in attr_target_set:
    #         #     tp_attr_city_page.delay(line[4],line[0])
    #         # if line[0] in rest_target_set:
    #         #     tp_rest_city_page.delay(line[4],line[0])
    #         # if line[0] in shop_target_set:
    #         #     tp_shop_city_page.delay(line[4], line[0])
    #         tp_attr_city_page.delay(line[4], line[0])
    #         tp_rest_city_page.delay(line[4], line[0])
    #         tp_shop_city_page.delay(line[4], line[0])
    #         _count += 1
    #         # tp_attr_list_page_num.delay(line[-1], line[0])
    # print _count

    # todo hotel_base_data init
    # import db_localhost
    #
    #
    # # def get_task():
    # #     sql = 'select source,source_id,city_id,hotel_url from adding.hotelinfo_zls_lx20161226'
    # #     for line in db_198_139.QueryBySQL(sql):
    # #         if line['source'] != 'booking':
    # #             continue
    # #         other_info = {
    # #             'source_id': line['source_id'],
    # #             'city_id': line['city_id']
    # #         }
    # #         yield line['source'], line['hotel_url'], other_info
    #
    # def get_task():
    #     sql = 'select source,source_id,city_id,hotel_url,map_info from hotel_adding.hotelinfo_static_data'
    #     for line in db_localhost.QueryBySQL(sql):
    #         if line['map_info'] != 'NULL':
    #             continue
    #         other_info = {
    #             'source_id': line['source_id'],
    #             'city_id': line['city_id']
    #         }
    #         yield line['source'], line['hotel_url'], other_info
    #
    #
    # def get_finished():
    #     _set = set()
    #     sql = 'select hotel_url from hotel_adding.hotelinfo_static_data'
    #     for line in db_localhost.QueryBySQL(sql):
    #         _set.add(line['hotel_url'])
    #     return _set
    #
    #
    # already_downloaded = get_finished()

    # def get_task_new():
    #     # sql = 'select source,source_id,city_id,hotel_url,map_info from hotel_adding.room_sid_monitor'
    #     sql = 'select * from hotel_adding.room_sid_monitor where source!="hostelworld"'
    #     for line in db_localhost.QueryBySQL(sql):
    #         if line['hotel_url'] not in already_downloaded:
    #             other_info = {
    #                 'source_id': line['sid'],
    #                 'city_id': line['mid']
    #             }
    #             yield line['source'], line['hotel_url'], other_info

    #
    # from proj.hotel_tasks import hotel_base_data
    #
    # _count = 0
    # for source, sid, other_info in get_task():
    #     _count += 1
    #     hotel_base_data.delay(source, sid, other_info)
    # print _count

    # todo poi_pic_spider test
    # from proj.poi_pic_spider_tasks import flickr_spider,google_spider,shutter_spider

    # google_spider('v223163','阿布洛霍斯群岛')
    # flickr_spider('v223163','东京塔')
    # shutter_spider('v223163','东京塔')

    # todo hotel base data init by Task
    # from proj.hotel_tasks import hotel_base_data
    #
    # _count = 0
    # for task_id, args in get_task('hotel_base_data'):
    #     hotel_base_data.delay(args['source'], args['hotel_url'], args['other_info'], task_id=task_id)
    #     _count += 1
    # print _count

    # todo get img by Task
    # from proj.tasks import get_images
    #
    # # source target_url task_id
    # _count = 0
    # for task_id, args in get_task('img_task', limit=60000):
    #     _count += 1
    #     get_images.delay(args['source'], args['target_url'], task_id=task_id)
    # print _count

    # todo poi_pic_list by Task
    # from proj.poi_pic_spider_tasks import google_spider, shutter_spider, flickr_spider
    #
    # _count = 0
    # for task_id, args in get_task('poi_pic_task', limit=30000):
    #     if args['source'] == 'google':
    #         google_spider.delay(args['mid'], args['keyword'], task_id=task_id)
    #     elif args['source'] == 'shutter':
    #         shutter_spider.delay(args['mid'], args['keyword'], task_id=task_id)
    #     elif args['source'] == 'flickr':
    #         flickr_spider.delay(args['mid'], args['keyword'], task_id=task_id)
    # print _count

    # todo hotel comment by Task

    # from proj.tasks import venere_comment, booking_comment, expedia_comment
    #
    # for task_id, args in get_task('hotel_comment', limit=30000):
    #     if args['source'] == 'booking':
    #         booking_comment.delay(args['target_url'])
    #     elif args['source'] == 'expedia':
    #         expedia_comment.delay(args['target_url'])
    #     elif args['source'] == 'venere':
    #         venere_comment.delay(args['target_url'])

    # todo qyer city parser test
    # from proj.qyer_city_tasks import qyer_spider
    #
    # qyer_spider('亚洲', 'Japan')

    # todo qyer poi task test
    # from proj.qyer_poi_tasks import qyer_poi_task
    # qyer_poi_task('http://place.qyer.com/poi/V2IJYVFlBzdTZg/',task_id='asdfasdf')

    # todo tripadvisor_city_query_test
    # from proj.tripadvisor_city_query_task import tripadvisor_city_query_task
    #
    # tripadvisor_city_query_task('巴黎', task_id='11111')

    # todo qyer_city_query test
    # from proj.qyer_city_query_task import qyer_city_query_task
    #
    # qyer_city_query_task('巴黎', task_id='12312')

    # from proj.qyer_city_spider import qyer_country_spider
    #
    # # qyer_city_spider(184L, u'USA', u'http://place.qyer.com/usa/')
    # qyer_country_spider(163L, u'http://place.qyer.com/the-bahamas/', task_id='55daba1d188b22766d235ba26bea2c23')

    # todo test get_images
    # from proj.tasks import get_images
    #
    # get_images.delay('test_img',
    #                  'https://www.google.com.sg/images/branding/googlelogo/2x/googlelogo_color_120x44dp.png', task_id='abcd∂ß')

    # todo test tripadvisor_city
    # from proj.tripadvisor_city import get_cities, get_task
    #
    # # get_cities('191', 143, 0)
    # for geo, country_id, offset in get_task():
    #     get_cities.delay(geo, country_id, offset)

    # todo test hotel_list_task
    # from proj.hotel_list_task import hotel_list_task, hotel_list_database
    #
    # # 21147 21378
    # # print hotel_list_database('hoteltravel', '21378')
    # # print hotel_list_database('elong', '21281')
    # # print hotel_list_database('hotels', '21029')
    # print hotel_list_database('booking', '13108')
    # hotel_list_task('hoteltravel', '21447', 'remote_4_test_hotel_list', task_id='asdfasdf')

    # todo test qyer poi task
    # from proj.qyer_attr_task import detail_page, get_pid_total_page
    #
    # target_url = u'http://place.qyer.com/paris/sight/'
    # # print get_pid_total_page.delay(target_url=target_url)
    #
    # # detail_page(u'20', 2)

    # get_pid_total_page(target_url=target_url, city_id=u'10001', part=u'qyer_test_0210')
    # detail_page(pid=u'20', page_num=10, city_id='10001', part='qyer_test_0214')

    # todo daodao poi task init
    # import pandas
    # import json
    # from sqlalchemy import create_engine
    # from proj.tasks import tp_attr_city_page, tp_rest_city_page, tp_shop_city_page
    # from proj.my_lib.task_module.task_func import insert_task, get_task_id
    #
    # engine = create_engine('mysql+mysqlconnector://hourong:hourong@localhost:3306/SuggestName')
    #
    # table = pandas.read_sql(
    #     'select city_id, daodao_url from DaodaoSuggestCityUrl where daodao_url!="null" and daodao_url!="无" and daodao_url!="-" and city_id in ("10161", "10352", "10381", "10386", "10468", "10551", "11423", "11446", "11471", "11481", "11487", "11491", "11566", "11612", "11615", "11618", "11625", "11628", "11631", "11653", "11666", "11696", "11716", "11740", "11757", "11758", "11773", "11802", "11850", "11862", "11863", "11869", "11875", "11881", "11885", "11886", "11900", "11906", "11912", "11921", "11941", "11944", "11958", "11988", "12006", "12008", "12014", "12034", "12036", "12038", "12045", "12074", "12102", "12109", "12117", "12146", "12157", "12171", "12246", "12249", "12252", "12305", "12323", "12326", "12386", "12407", "12423", "12432", "12443", "12449", "12453", "12476", "12481", "12482", "12494", "12561", "12623", "12627", "12636", "12644", "12725", "12733", "12749", "12754", "12763", "12771", "12795", "12824", "12835", "12852", "12921", "12949", "12950", "12956", "12961", "12964", "12966", "12972", "12976", "12993", "13007", "13010", "13015", "13023", "13025", "13028", "13035", "13039", "13069", "13078", "13168", "13173", "13178", "13181", "13184", "13187", "13216", "13217", "13221", "13222", "13238", "13257", "13259", "13273", "13281", "13300", "13335", "13385", "13389", "13422", "13425", "13429", "13434", "13446", "13474", "20045", "20093", "20199", "20214", "20215", "20222", "20230", "20236", "20314", "20328", "20353", "20358", "20364", "20374", "20407", "20409", "20413", "20423", "20463", "20492", "20506", "20511", "20545", "20555", "20558", "20561", "20564", "20568", "20570", "20586", "20635", "20641", "20650", "20678", "20680", "20707", "20727", "20736", "20744", "20763", "20768", "20807", "20858", "20877", "20887", "20895", "20946", "20962", "20967", "21001", "21051", "21094", "21109", "21121", "21158", "21159", "21161", "21171", "21177", "21188", "21189", "21194", "21198", "21200", "21227", "21235", "21250", "21263", "21279", "21284", "21287", "21331", "21335", "21339", "21341", "21344", "21347", "21350", "21355", "21358", "21361", "21364", "21383", "21392", "21397", "21398", "21412", "21417", "21419", "21441", "21443", "21455", "21459", "30078", "30082", "30090", "30100", "30101", "30114", "30165", "30170", "30172", "30175", "30184", "30187", "30195", "30208", "30220", "30225", "30237", "30244", "30246", "30247", "30253", "30272", "30294", "30300", "30301", "30309", "30310", "30319", "30326", "30331", "30332", "40040", "40043", "40061", "40064", "40065", "40075", "40091", "40120", "40122", "40123", "40126", "40141", "40158", "40170", "40184", "40194", "40199", "40208", "40220", "40229", "40267", "40269", "40288", "40297", "40333", "40352", "40354", "40362", "40366", "40369", "40390", "40393", "40434", "40450", "40456", "40461", "40463", "40469", "50060", "50062", "50063", "50065", "50068", "50079", "50081", "50130", "50142", "50170", "50194", "50219", "50331", "50399", "50463", "50590", "50594", "50696", "50750", "50753", "50771", "50801", "50804", "50818", "50840", "50895", "50901", "50911", "50917", "50921", "50925", "50929", "50954", "51026", "51057", "51105", "51115", "51132", "51138", "51143", "51154", "51157", "51174", "51178", "51207", "51211", "51227", "51305", "51322", "51353", "51354", "51359", "51365", "51371", "51383", "51403", "51421", "51450", "60002", "60075", "60082", "60122", "60137")',
    #     engine)
    # city_id_dict = pandas.Series(table.daodao_url.values, table.city_id).to_dict()
    #
    # data = []
    # worker = u'daodao_poi_base_data'
    #
    # for k, v in city_id_dict.items():
    #     if u'Tourism' in v:
    #         tp_attr_city_page.delay(v.strip(), k, 'tp_attr_list_0216')
    #         tp_rest_city_page.delay(v.strip(), k, 'tp_rest_list_0216')
    #         tp_shop_city_page.delay(v.strip(), k, 'tp_shop_list_0216')
    #
    #     if u'Attraction_Review' in v:
    #         args = json.dumps(
    #             {u'target_url': unicode(v.strip()), u'city_id': unicode(k), u'type': 'attr'})
    #         task_id = get_task_id(worker, args=args)
    #         data.append((task_id, worker, args, u'tp_attr_detail_0216'))
    #
    # print insert_task(data=data)

    # todo qyer poi task init
    # import pandas
    # from sqlalchemy import create_engine
    # from proj.qyer_attr_task import get_pid_total_page
    #
    # engine = create_engine('mysql+mysqlconnector://hourong:hourong@localhost:3306/SuggestName')
    #
    # table = pandas.read_sql('select city_id, city_link from qyer_id_2', engine)
    # city_id_dict = pandas.Series(table.city_link.values, table.city_id).to_dict()
    # for k, v in city_id_dict.items():
    #     target_url = unicode(v + 'sight/')
    #     city_id = unicode(k)
    #     print target_url, city_id
    #     get_pid_total_page.delay(target_url=target_url, city_id=city_id, part='tp_qyer_list_0214')

    # todo test poi nearby city task
    # # from proj.poi_nearby_city_task import poi_nearby_city_task
    #
    # # poi_id = 'v223168'
    # # city_id = '30010'
    # # map_info = '151.212531,-33.866978'
    # # poi_nearby_city_task(poi_id=poi_id, poi_city_id=city_id, poi_map_info=map_info)
    #
    # import pymysql
    # from proj.poi_nearby_city_task import poi_nearby_city_task
    #
    # conn = pymysql.connect(host='10.10.189.213', user='hourong', passwd='hourong', charset='utf8', db='onlinedb')
    #
    # # _count = 0
    # # with conn as cursor:
    # #     cursor.execute('select id, city_id, map_info from chat_restaurant')
    # #     for mid, m_city_id, map_info in cursor.fetchall():
    # #         poi_nearby_city_task.delay(poi_id=mid, poi_city_id=m_city_id, poi_map_info=map_info, task_id='abcd')
    #
    #
    # _count = 0
    # with conn as cursor:
    #     cursor.execute('select uid, city_mid, map_info from hotel limit 1500000,500000')
    #     for mid, m_city_id, map_info in cursor.fetchall():
    #         poi_nearby_city_task.delay(poi_id=mid, poi_city_id=m_city_id, poi_map_info=map_info, task_id='abcd')
    #         _count += 1
    # print _count

    # todo test_daodao_img_rename task

    # def get_task():
    #     f = open('/root/data/task/attr_img_task_170223')
    #     _count = 0
    #     for line in f:
    #         try:
    #             mid, img_url, file_name = line.strip().split('\t')
    #         except:
    #             continue
    #         if mid != '':
    #             _count += 1
    #             yield mid, img_url, file_name + '.jpg'
    #             if _count == 10:
    #                 break
    #
    #
    # from proj.daodao_img_rename_tasks import daodao_img_rename_task
    #
    # # (self, file_name, src_path, dst_path, bucket_name, img_url, mid, table_name, **kwargs)
    # _count = 0
    # for mid, img_url, file_name in get_task():
    #     try:
    #         daodao_img_rename_task(file_name, '/search/image/attr_img_task_170223', '/search/image/attr_result_0228',
    #                                'mioji-attr', img_url, mid, 'attr_bucket_relation', task_id='asdfasdf')
    #     except:
    #         continue
    #     _count += 1
    # print _count

    # from proj.daodao_img_rename_tasks import daodao_img_rename_task

    # task_args = {"file_name": "de60f0270dbc50680198e5d973394d84.jpg", "mid": "v237112",
    #              "dst_path": "/search/image/attr_result_0228", "table_name": "attr_bucket_relation",
    #              "src_path": "/search/image/attr_img_task_170223",
    #              "img_url": "http://ccm.ddcdn.com/ext/photo-s/0d/b6/03/13/photo1jpg.jpg", "bucket_name": "mioji-attr"}

    # task_args = {"file_name": "c5a16c87624fe8dd0bb0fb3402f1285e.jpg", "mid": "v628073",
    #              "dst_path": "/search/image/attr_result_0228", "table_name": "attr_bucket_relation",
    #              "src_path": "/search/image/attr_img_task_170223",
    #              "img_url": "http://ccm.ddcdn.com/ext/photo-s/0d/56/32/30/overlook.jpg", "bucket_name": "mioji-attr"}
    # daodao_img_rename_task(task_id='106cec6e450bb7afc3d5ad79d5cc3cd6', **task_args)

    # todo test hotel parser
    # from proj.hotel_tasks import hotel_base_data
    #
    # source = u'booking'
    # other_info = {
    #     u'source_id': u'1781737',
    #     u'city_id': u'10427'
    # }
    # hotel_url = u'http://www.booking.com/hotel/ee/aarde-apartments.zh-cn.html?label=gen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmcgV1c19kZYgBAZgBMsIBA2FibsgBDNgBA-gBAagCBA;sid=182e979b96ee436b39da0638a459a059;checkin=2017-04-03;checkout=2017-04-04;ucfs=1;highlighted_blocks=178173702_97225128_2_0_0;all_sr_blocks=178173702_97225128_2_0_0;room1=A,A;hpos=12;dest_type=city;dest_id=-2625660;srfid=03110f676da63ae2e0d632d5ad163716751ccedeX267;highlight_room='
    # hotel_base_data(source, hotel_url, other_info, u'test123')
