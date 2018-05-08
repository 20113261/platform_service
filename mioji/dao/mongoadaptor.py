#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymongo

client = pymongo.MongoClient('10.10.129.187', 27017)
request_raw = client.archive.request_raw


def do_insert(req_host, real_ip, ua, result):
    # req_hsot 请求的域名
    # real_ip 真实 ip
    # ua
    # result  0 or 1
    document = {'host': req_host,
                'ip': real_ip,
                'UserAgent': ua,
                'result': result
                }
    request_raw.insert_one(document)


if __name__ == '__main__':
    do_insert('mioji.com', '10.10.156.116', 'mioji bot', 0)
    print 'done'
