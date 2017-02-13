import json
from collections import defaultdict

import db_114_35_attr
import db_114_35_rest
import db_114_35_shop
import db_localhost
import db_test
import re

pattern = re.compile('-d(\d+)')


def get_comment_count(s_type):
    if s_type == 'attr':
        hname = 'view'
    elif s_type in ['shop', 'rest', 'hotel']:
        hname = s_type
    else:
        raise TypeError()
    comment_count = defaultdict(int)
    sql = 'select id,count from comment_count where hname="{0}"'.format(hname)
    for line in db_test.QueryBySQL(sql):
        comment_count[line['id']] = int(line['count'])
    return comment_count


def get_task(s_type):
    city_limitation = ' where city_id in ("10415","11534","11555","20045","10423","10426","11512","10427","10024","10059","10158","10242","10428","11529","11530","11531","11532","11552","11557","11560","10443","10109","10281","10300","11322","11527","11543","11548","10039","10110","10123","10133","10135","10140","10180","10192","10194","10408","10483","11123","11266","11517","11518","11541","11546","11553","11556","11564","10487","10494","10094","10147","10182","10199","10226","10249","10729","11338","11365","11537","11554","10141","10230","10075","10540","11535","11545","11550","11558","11561","11563","10055","10126","10152","10222","10315","10324","10541","11211","11549","11559","10549","10550","10551","10553","11528","10555","10556","11516","10561","11522","11523","11524","11525","11096","10186","10190","11544","10402","11070","10066","10080","10137","10155","10187","10272","10282","10303","10384","10388","11164","11413","11533","11536","11547","11562","11526","10598","10615","11488","11519","11520","11521","11542","10058","10060","10087","10129","10205","11429","10314","11300","11540","10067","10069","10125","10130","10150","10163","10183","10208","10210","10219","10221","10224","10263","10275","10356","10656","11106","11269","11513","11514","11515","11538","11539","10040","10044","10105","10139","10162","10232","10674","10680","10683","11010","11398","11405","11468","11551","20393")'
    if s_type == 'attr':
        sql = 'select id,url from chat_attraction' + city_limitation
    elif s_type == 'rest':
        sql = 'select id,res_url from chat_restaurant' + city_limitation
    elif s_type == 'shop':
        sql = 'select id,url from chat_shopping' + city_limitation
    else:
        raise TypeError()

    if s_type in ['attr', 'shop']:
        if s_type == 'attr':
            database = db_114_35_attr
        elif s_type == 'shop':
            database = db_114_35_shop
        else:
            raise TypeError()
        for line in database.QueryBySQL(sql):
            url = line['url']
            if 'Attraction_Review' in url:
                for v in json.loads(url).values():
                    if 'Attraction_Review' in str(v):
                        yield line['id'], 'http://www.tripadvisor.cn/' + str(v).split('/', 3)[-1]
    if s_type == 'rest':
        database = db_114_35_rest
        for line in database.QueryBySQL(sql):
            url = line['res_url']
            if 'Restaurant_Review' in url:
                yield line['id'], 'http://www.tripadvisor.cn/' + url.split('/', 3)[-1]


def get_ready_id():
    id_set = set()
    sql = 'select distinct miaoji_id from attr_comment_0105'
    for line in db_localhost.QueryBySQL(sql):
        id_set.add(line['miaoji_id'])
    return id_set


def get_task_full(s_type):
    id_set = get_ready_id()
    for mid, url in get_task(s_type):
        if mid not in id_set:
            yield mid, url


if __name__ == '__main__':
    comment_count = get_comment_count('rest')
    count = 0
    url_set = set()
    for mid, url in get_task('rest'):
        if not comment_count[mid]:
            # print mid, url
            url_set.add(url)
            count += 1
    print count
    print len(url_set)
