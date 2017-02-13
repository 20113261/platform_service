import json

import db_localhost

import database


def get_task(s_type):
    if s_type == 'attr':
        sql = 'select id,url from chat_attraction where image_list=""'
    elif s_type == 'rest':
        sql = 'select id,res_url from chat_restaurant where image_list=""'
    elif s_type == 'shop':
        sql = 'select id,url from chat_shopping where image_list=""'
    else:
        raise TypeError()

    if s_type in ['attr', 'shop']:
        for line in database.QueryBySQL(sql):
            url = line['url']
            if 'Attraction_Review' in url:
                for v in json.loads(url).values():
                    if 'Attraction_Review' in str(v):
                        yield line['id'], 'http://www.tripadvisor.cn/' + str(v).split('/', 3)[-1]
    if s_type == 'rest':
        for line in database.QueryBySQL(sql):
            url = line['res_url']
            if 'Restaurant_Review' in url:
                yield line['id'], 'http://www.tripadvisor.cn/' + url.split('/', 3)[-1]


def already_crawl():
    mid_set = set()
    sql = 'select mid from image_recrawl'
    for line in db_localhost.QueryBySQL(sql):
        mid_set.add(line['mid'])
    return mid_set


def get_task_full(s_type):
    already_crawl_set = already_crawl()
    for mid, url in get_task(s_type):
        if mid not in already_crawl_set:
            yield mid, url


if __name__ == '__main__':
    import random

    url_set = set()
    for mid, url in get_task_full('rest'):
        url_set.add(url)
    l_url = list(url_set)
    random.shuffle(l_url)
    print len(url_set)
    for i in l_url[:10]:
        print i
