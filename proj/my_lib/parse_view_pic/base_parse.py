#!/usr/bin/env python
# encoding:utf-8

'''
author: dongkai
create date: 2017-01-10
update date: 2017-01-11
'''

import json
import sys
import time
from pprint import pprint

import requests
from lxml import etree as ET

reload(sys)
sys.setdefaultencoding("utf-8")


def save_html(response, file_name=None):
    """
    save response html info
    """
    if file_name is None:
        file_name = time.strftime("%s") + ".html"
    with open(file_name, "w") as html_file:
        html_file.write(response)


def save_response(response, resp_source, file_name=None,
                  file_type="html"):
    """
    save spider pic response No return
    """
    if file_name is None:
        file_index = str(int(time.time() * 1000))
    else:
        file_index = file_name

    file_name = "{0}.{1}.{2}".format(resp_source, file_index, file_type)
    with open(file_name, "w") as html_file:
        html_file.write(response)


class GooglePicSpider(object):
    '''
    Google Picture Spider
    '''

    def __init__(self, search_word, google_proxy, debug=False):
        self.session_conn = requests.session()
        self.uri = "https://www.google.com.hk/search"
        self.proxy = {"https": google_proxy,
                      "http": google_proxy}
        self.search_kw = search_word
        self.ijn = 0
        self.headers = {"Referer": "https://www.google.com.hk",
                        "accept-encoding": "gzip, deflate, sdch, br",
                        "accept-language": "zh-CN,zh;q=0.8",
                        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36",
                        }
        self.debug = debug

    def _http_req(self, args, uri=None, headers=None):
        """
        """
        if headers:
            self.headers.update(headers)
        if uri is None:
            uri = self.uri
        search_conn = self.session_conn.get(uri,
                                            params=args,
                                            headers=self.headers,
                                            proxies=self.proxy)
        if self.debug:
            save_response(search_conn.text, "google")
        return search_conn.text

    def pic_search(self):
        """
        Google图片关键字搜索与内容检索
        """
        # 缺失 gs_l 参数
        search_args = {"newwindow": 1,
                       "safe": "strict",
                       "hl": "zh-CN",
                       "biw": 1440,
                       "bih": 768,
                       "site": "imghp",  # 搜索类型关键字
                       "tbs": "isz:lt,islt:xga,sur:fmc",
                       "tbm": "isch",
                       "sa": 1,
                       "q": self.search_kw,
                       "oq": self.search_kw
                       }

        page_text = self._http_req(search_args)

        page_html = ET.HTML(page_text.decode("utf-8"))

        # data ved info 翻页时候所使用的信息
        data_ved_path = '//div[@id="rg"]'
        ved_info_list = page_html.xpath(data_ved_path)
        if len(ved_info_list):
            data_ved = ved_info_list[0].get("data-ved")
        else:
            data_ved = None

        self.data_ved = data_ved

        # eid info 翻页时候所使用的信息
        eid_path = '//div[@id="rso"]'
        eid_info_list = page_html.xpath(eid_path)
        if len(eid_info_list):
            eid = eid_info_list[0].get("eid")
        else:
            eid = None

        self.eid = eid

        # meta info
        pic_meta_path = '//div[@class="rg_meta"]/text()'
        # 单次返回页面中meta信息长度为100
        page_meta_list = page_html.xpath(pic_meta_path)
        pic_meta = [json.loads(x) for x in page_meta_list]
        self.start_int = len(pic_meta)
        # 单个图片的json信息
        """
        {u'cr': 3,
         u'id': u'pS9zLo3ypRb_5M:',
         u'isu': u'zh.wikipedia.org',
         u'itg': False,
         u'ity': u'jpg',
         u'oh': 1536,
         u'ou': u'https://upload.wikimedia.org/wikipedia/commons/3/3c/Shinjuku_2006-02-22_a.jpg',
         u'ow': 2048,
         u'pt': u'\u4e1c\u4eac- \u7ef4\u57fa\u767e\u79d1\uff0c\u81ea\u7531\u7684\u767e\u79d1\u5168\u4e66',
         u'rid': u'_17k4ANObJp1aM',
         u'ru': u'https://zh.wikipedia.org/wiki/%E4%B8%9C%E4%BA%AC',
         u's': u'\u6771\u4eac\u7d93\u6fdf\u5708\u7531\u9435\u8def\u5e36\u52d5',
         u'st': u'\u7ef4\u57fa\u767e\u79d1',
         u'th': 194,
         u'tu': u'https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcQON04v_a3pRol8eg-5PImwGWxoZQLRG1qivRNTakNmxVnjaN28dA',
         u'tw': 259}
        """
        return pic_meta

    def pic_scroll_page(self):
        """
        发送翻页请求，翻页请求类型为XHR， 返回内容为字符串，解析字符串获得结果
        """
        # 翻页标记
        self.ijn += 1
        search_args = {"async": "_id:rg_s,_pms:s",
                       "ei": self.eid,
                       "yv": 2,
                       "q": self.search_kw,
                       "start": self.start_int,
                       "asearch": "ichunk",
                       "newwindow": 1,
                       "safe": "strict",
                       "tbm": "isch",
                       "vet": "1{0}.{1}.i".format(self.data_ved, self.eid),
                       "ved": self.data_ved,
                       "ijn": self.ijn
                       }
        pprint(search_args)
        search_conn = self.session_conn.get(self.uri,
                                            params=search_args,
                                            headers=self.headers,
                                            proxies=self.proxy)
        pprint(search_conn.url)
        if self.debug:
            save_html(search_conn.text, "scroll_page.resp")

        pprint(search_conn.text)


class FlickrPicSpider(object):
    """
    """

    def __init__(self, search_kw, proxy=None, debug=False, *args):
        self.session_conn = requests.session()
        self.uri = "https://www.flickr.com/search/"
        self.proxy = {"https": proxy,
                      "http": proxy}
        self.search_kw = search_kw
        self.headers = {"accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "accept-encoding": "gzip, deflate, sdch, br",
                        "accept-language": "zh-CN,zh;q=0.8",
                        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36",
                        }
        self.debug = debug

    def _http_req(self, args, uri=None, headers=None):
        """
        """
        if headers:
            self.headers.update(headers)
        if uri is None:
            uri = self.uri
        search_conn = self.session_conn.get(uri,
                                            params=args,
                                            headers=self.headers,
                                            proxies=self.proxy)
        if self.debug:
            save_response(search_conn.text, "flickr", file_type="json")
        return search_conn.text

    def html_search(self, **kwargs):
        """
        """
        search_args = {"text": self.search_kw,
                       "dimension_search_mode": "min",
                       "height": 1024,
                       "width": 1024,
                       "license": "4,5,6,9,10"}
        page_str = self._http_req(search_args)
        api_key = page_str.split("root.YUI_config.flickr.api.site_key = ", 1)[
            1].split(";")[0].strip('"')
        req_id = page_str.split("root.reqId = ", 1)[1].split(";")[0].strip('"')

        return (api_key, req_id)

    def pic_search(self, page=1, per_page=100):
        """
        """
        flickr_key = self.html_search()
        args = {"sort": "relevance",
                "parse_tags": 1,
                "contente_type": 7,
                "extras": "description,license,media,url_l,url_m,url_n,url_q",
                "per_page": per_page,
                "page": page,
                "lang": "zh-Hant-HK",
                "text": self.search_kw,
                "dimension_search_mode": "min",
                "height": 1024,
                "width": 1024,
                "license": "4,5,9,10",
                "method": "flickr.photos.search",
                "api_key": flickr_key[0],
                "reqId": flickr_key[1],
                "format": "json",
                "hermes": 1,
                "hermesClient": 1,
                "nojsoncallback": 1}
        api_url = "https://api.flickr.com/services/rest"
        api_resp = self._http_req(args, api_url)

        resp_json = json.loads(api_resp)

        return resp_json


class ShutterShockPicSpider(object):
    """docstring for ShutterShockPicSpider"""

    def __init__(self, search_kw, proxy=None, debug=False):
        super(ShutterShockPicSpider, self).__init__()
        self.session_conn = requests.session()
        self.uri = "https://www.shutterstock.com/search"
        self.proxy = {"https": proxy,
                      "http": proxy}
        self.search_kw = search_kw
        self.page = 0
        self.headers = {"Referer": "https://www.shutterstock.com/search",
                        "accept-encoding": "gzip, deflate, sdch, br",
                        "accept-language": "zh-CN,zh;q=0.8",
                        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36",
                        }
        self.debug = debug

    def _generate_link(self, html_link):
        """
        """
        big_img_url = "https://image.shutterstock.com/z/"
        thumb_link = "https:" + html_link
        big_link = big_img_url + html_link.split("/")[-1]
        return {"thumb_link": thumb_link,
                "large_link": big_link}

    def _http_req(self, args, uri=None, headers=None):
        """
        """
        if headers:
            self.headers.update(headers)
        if uri is None:
            uri = self.uri
        search_conn = self.session_conn.get(uri,
                                            params=args,
                                            headers=self.headers,
                                            proxies=self.proxy)
        if self.debug:
            save_response(search_conn.text, "shutter")
        return search_conn.text

    def pic_search(self):
        """
        """
        self.page += 1
        search_args = {"searchterm": self.search_kw,
                       "sort": "popular",
                       "image_type": "all",
                       "search_source": "search_source:base_search_form",
                       "language": "zh",
                       "page": self.page}
        page_str = self._http_req(search_args)

        if self.debug:
            save_response(page_str)

        html_page = ET.HTML(page_str.decode("utf-8"))
        img_path = "//img[@src][@alt][name(..)='div'][../@class='img-wrap']"
        search_ret = html_page.xpath(img_path)
        img_link_list = []
        for img_item in search_ret:
            html_link = img_item.get("src")
            if html_link is None:
                continue
            img_link_list.append(self._generate_link(html_link))
        return img_link_list


if __name__ == "__main__":
    proxy = None
    kw = "东京塔"
    flickr_spider = FlickrPicSpider(kw, proxy, True)
    print flickr_spider.pic_search()
    # shutter_spider = ShutterShockPicSpider(kw, proxy, True)
    # for i in range(3):
    # print shutter_spider.pic_search()
    # flickr_spider = FlickrPicSpider(kw, proxy, True)
    # print flickr_spider.api_search()

    # google_spider = GooglePicSpider(kw, proxy, True)
    # f_ret = google_spider.pic_search()
    # google_spider.pic_scroll_page()
