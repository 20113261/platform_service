#!/usr/bin/env python
# -*-coding:utf-8 -*-

from sqlalchemy.sql import text

from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.Common.Utils import retry
import requests
import json
import pymongo
from datetime import datetime
import types
MONGODB_CONFIG = {
    'host': '10.10.213.148'
}


class AllSuggestCitySDK(BaseSDK):

    @retry(times=5)
    def _execute(self, **kwargs):
        try:
            spider = self.task.kwargs['spider']
            collection_name = self.task.kwargs['collection_name']
            key_word = self.task.kwargs['keyword']
            source = spider.ticket_info.get('source')
            content_type = self.task.kwargs['content_type']

            spider.task.ticket_info['keyword'] = key_word
            client = pymongo.MongoClient(**MONGODB_CONFIG)
            collection = client['CitySuggest'][collection_name]
            spider.crawl()
            values = list(spider.result.values())

            for value in values:
                if isinstance(value,(types.DictType,types.ListType)):
                    collection.insert(value)
                else:
                    content = {'suggest':value}
                    collection.insert(content)
            if len(values) >= 0:
                self.finished_error_code = 0

        except requests.RequestException as e:
            raise ServiceStandardError(ServiceStandardError.REQ_ERROR,e.message)
        except Exception as e:
            raise ServiceStandardError(ServiceStandardError.MONGO_ERROR,e.message)


if __name__ == "__main__":
    pass