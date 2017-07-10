#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/9 下午11:00
# @Author  : Hou Rong
# @Site    : 
# @File    : init_full_site_task.py
# @Software: PyCharm
import pymongo
import datetime

from proj.celery import app

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['Task']['FullSite']

if __name__ == '__main__':
    kwargs = {}
    for line in collections.find({"website_url": {"$in": ["http://www.castillosanfernando.org/",
                                                          "http://www.kazanski-sobor.ru",
                                                          "http://malacanang.gov.ph/last-days-of-rizal-and-his-burial",
                                                          "http://www.toledo-turismo.com/turismo/contenido/conociendo-la-ciudad/donde-mirar/monumentos/puentes/puente-san-martin.aspx",
                                                          "http://www.chateauversailles-spectacles.fr/spectacles/2015/concerts-saison-2015-2016",
                                                          "http://silt.coop@tiscali.it",
                                                          "http://www.turismo.intoscana.it/site/it/elemento-di-interesse/Piazza-Grande-Arezzo/",
                                                          "http://akuaku.ru/dostoprimechatelnosti/pushkinskaia-ploshchad",
                                                          "http://www.centrepompidou-metz.fr/",
                                                          "http://www.laccanhdainamvanhien.vn/home.htm"]},
                                  "mid": {"$ne": "v534690"}}):
        mid = line['mid']
        website_url = line['website_url']
        print mid,website_url
        app.send_task('proj.full_website_spider_task.full_site_spider',
                      args=(website_url, 0, website_url, {'id': mid},),
                      kwargs=kwargs,
                      queue='full_site_task',
                      routing_key='full_site_task')
