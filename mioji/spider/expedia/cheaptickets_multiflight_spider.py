#!/usr/bin/env python
# -*- coding: utf-8 -*-

from multiFlight_base_class import BaseMultiFlightSpider


class cheapticketsMultiFlightSpider(BaseMultiFlightSpider):
    source_type = 'cheapticketsMultiFlight'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'MultiFlight': {'version': 'InsertMultiFlight'}
    }

    def __init__(self, task=None):
        BaseMultiFlightSpider.__init__(self, task)

        self.source = 'cheaptickets'
        self.host = 'https://www.cheaptickets.com'

    old_spider_tag = {
        'cheapticketsMultiFlight': {'required': ['MultiFlight']}
    }