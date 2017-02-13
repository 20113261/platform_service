import json

import database
import db_localhost


def finish_set():
    qyer_set = set()
    sql = 'select url from qyer_img'
    for line in db_localhost.QueryBySQL(sql):
        qyer_set.add(line['url'])
    return qyer_set


def get_task():
    qyer_set = finish_set()
    sql = 'select id,url from chat_attraction'
    for line in database.QueryBySQL(sql):
        for v in json.loads(line['url']).values():
            if 'place.qyer.com' in str(v):
                if v.endswith('/'):
                    img_url = v + 'photo'
                else:
                    img_url = v + '/photo'
                if img_url not in qyer_set:
                    yield line['id'], img_url


if __name__ == '__main__':
    import random

    a = [i for i in get_task()]
    random.shuffle(a)
    for i, u in a[:10]:
        print i, u
