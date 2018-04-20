#!/usr/bin/env python
# -*- coding: utf-8 -*-
from roundFlight_base_class import BaseRoundFlightSpider


class travelocityRoundFlightSpider(BaseRoundFlightSpider):
    source_type = 'travelocityRoundFlight'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'RoundFlight': {'version': 'InsertRoundFlight2'}
    }

    def __init__(self, task=None):
        BaseRoundFlightSpider.__init__(self, task)

        self.source = 'travelocity'
        self.host = 'https://www.travelocity.com'

    old_spider_tag = {
        'travelocityRoundFlight': {'required': ['RoundFlight']}
    }

