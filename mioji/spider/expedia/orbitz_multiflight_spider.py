#!/usr/bin/env python
# -*- coding: utf-8 -*-

from multiFlight_base_class import BaseMultiFlightSpider


class cheapticketsMultiFlightSpider(BaseMultiFlightSpider):
    source_type = 'orbitzMultiFlight'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'MultiFlight': {'version': 'InsertMultiFlight'}
    }

    def __init__(self, task=None):
        BaseMultiFlightSpider.__init__(self, task)

        self.source = 'orbitz'
        self.host = 'https://www.orbitz.com'

    old_spider_tag = {
        'orbitzMultiFlight': {'required': ['MultiFlight']}
    }