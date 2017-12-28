#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/28 下午8:56
# @Author  : Hou Rong
# @Site    : 
# @File    : mongo_pool.py
# @Software: PyCharm
import pymongo
from proj import config

mongo_data_client = pymongo.MongoClient(config.MONGO_DATA_URL)