#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import simplejson as json

from Queue import Queue
from huantaoyouAPI import HuantaoyouApi

with open('wanle') as fp:
    all = json.load(fp)

local_queue = Queue()

for item in all:
    local_queue.put(item)

print 'local queue size is', local_queue.qsize()


is_duplicated = set()
poi_collection = []
fault_collection = []


def run(api, pid):
    resp = api.get_json(pid)
    try:
        poi_raw = get_consumer_terminal(resp)
        if not poi_raw or poi_raw['english_name'] in is_duplicated:
            return
        poi_collection.append(poi_raw)
    except KeyError:
        fault_collection.append(pid)


def get_consumer_terminal(local_json):
    return local_json['data']['consumer_terminal']


if __name__ == '__main__':
    api = HuantaoyouApi()
    while not local_queue.empty():
        ticket = local_queue.get()
        print 'handling', ticket['id'], 'result queue size =',
        run(api, ticket['id'])
        print local_queue.qsize()
    with io.open('poi_collection', 'w', encoding='utf8') as fp:
        fp.write(json.dumps(poi_collection, indent=2, ensure_ascii=False))
    print fault_collection
