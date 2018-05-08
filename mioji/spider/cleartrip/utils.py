#!/usr/bin/env python
# -*- coding: utf-8 -*-

# E经济舱、B商务舱、F头等舱、P超级经济舱
query_cabin_dict = {'E': 'Economy', 'B': 'Business', 'F': 'First', 'P': 'Premium+Economy'}


def seat_type_to_queryparam(seat_type):
    return query_cabin_dict.get(seat_type, 'Economy')