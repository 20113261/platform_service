# coding=utf-8
from __future__ import absolute_import

import json
import re

import db_localhost
from lxml import html


# def image_paser(content, url):
#     dom = html.fromstring(content)
#     result = ''
#     if len(dom.find_class('flexible_photo_wrap')) != 0:
#         try:
#             raw_text = dom.find_class('flexible_photo_album_link')[0].find_class('count')[0].xpath('./text()')[0]
#             image_num = re.findall('\((\d+)\)', raw_text)[0]
#             pattern = re.compile('var lazyImgs = ([\s\S]+?);')
#             google_list = []
#             img_url_list = []
#             if len(pattern.findall(content)) != 0:
#                 for each_img in json.loads((pattern.findall(content)[0]).replace('\n', '')):
#                     img_url = each_img[u'data']
#                     if 'ditu.google.cn' in img_url:
#                         google_list.append(img_url)
#                     elif 'photo-' in img_url:
#                         img_url_list.append(img_url.replace('photo-l', 'photo-s').replace('photo-f', 'photo-s'))
#
#             result = '|'.join(img_url_list[:int(image_num)])
#             print 'image_urls: ', result
#         except:
#             try:
#                 image_num = len(dom.find_class('flexible_photo_wrap'))
#                 pattern = re.compile('var lazyImgs = ([\s\S]+?);')
#                 google_list = []
#                 img_url_list = []
#                 if len(pattern.findall(content)) != 0:
#                     for each_img in json.loads((pattern.findall(content)[0]).replace('\n', '')):
#                         img_url = each_img[u'data']
#                         if 'ditu.google.cn' in img_url:
#                             google_list.append(img_url)
#                         elif 'photo-' in img_url:
#                             img_url_list.append(img_url.replace('photo-l', 'photo-s').replace('photo-f', 'photo-s'))
#                 result = '|'.join(img_url_list[:image_num])
#             except:
#                 pass
#     return result


def insert_db(args):
    sql = 'insert into image_recrawl (`mid`,`url`,`img_list`) VALUES (%s,%s,%s)'
    return db_localhost.ExecuteSQL(sql, args)