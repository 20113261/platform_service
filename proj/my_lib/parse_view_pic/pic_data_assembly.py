#!/usr/bin/env python
# encoding:utf-8

import time
from hashlib import md5


def get_md5(calc_str):
    """
    """
    if isinstance(calc_str, str) or isinstance(calc_str, unicode):
        return md5(calc_str).hexdigest()
    else:
        return None


def google_pic_data_assembly(vid, search_kw, pic_list):
    """
    过滤，组装Google 图片搜索页面的数据。返回数据类型为 dict
    vid: str. chat-attraction table id
    search_kw: str. search key words
    pic_list: google pic spider return list data
    """
    search_time = time.strftime("%Y-%m-%d %H:%M:%S")

    ret_map = {"thumb": {"fields": ["vid", "search_kw", "search_time",
                                    "pic_link", "pic_height", "pic_width",
                                    "link_md5"],
                         "values": [],
                         "table": "attraction_google_thumb_pic"
                         },
               "large": {"fields": ["vid", "search_kw", "search_time",
                                    "pic_link", "pic_height", "pic_width",
                                    "link_md5"],
                         "values": [],
                         "table": "attraction_google_large_pic"}
               }
    for pic_meta in pic_list:
        tb_link = pic_meta.get('tu')
        tb_link_md5 = get_md5(tb_link)
        temp_tb_list = [vid, search_kw, search_time, tb_link, pic_meta["th"],
                        pic_meta["tw"], tb_link_md5]
        ret_map["thumb"]["values"].append(temp_tb_list)

        large_link = pic_meta.get('ou')
        large_link_md5 = get_md5(large_link)
        temp_la_list = [vid, search_kw, search_time, large_link,
                        pic_meta["oh"], pic_meta["ow"], large_link_md5]
        ret_map["large"]["values"].append(temp_la_list)

    return ret_map


def flickr_pic_data_assembly(vid, search_kw, pic_map):
    """
    过滤，组装 flickr 图片搜索页面的数据。返回数据类型为 dict
    vid: str. chat-attraction table id
    search_kw: str. search key words
    pic_map: flickr pic spider return dict data
    """
    search_time = time.strftime("%Y-%m-%d %H:%M:%S")
    ret_map = {"thumb": {"fields": ["vid", "search_kw", "search_time",
                                    "pic_link", "pic_height", "pic_width",
                                    "link_md5"],
                         "values": [],
                         "table": "attraction_flickr_thumb_pic"},
               "large": {"fields": ["vid", "search_kw", "search_time",
                                    "pic_link", "pic_height", "pic_width",
                                    "link_md5"],
                         "values": [],
                         "table": "attraction_flickr_large_pic"
                         }
               }

    if pic_map.get("stat") == "ok":
        photos_map = pic_map.get("photos")
        pic_list = photos_map.get("photo", [])
    else:
        return ret_map

    for pic_meta in pic_list:
        tb_link = pic_meta.get("url_n_cdn")
        tb_link_md5 = get_md5(tb_link)
        temp_tb_list = [vid, search_kw, search_time, tb_link,
                        pic_meta["height_n"], pic_meta["width_n"], tb_link_md5]
        ret_map["thumb"]["values"].append(temp_tb_list)

        large_link = pic_meta.get('url_l_cdn')
        large_link_md5 = get_md5(large_link)
        temp_la_list = [vid, search_kw, search_time, large_link,
                        pic_meta["height_l"], pic_meta["width_l"],
                        large_link_md5]
        ret_map["large"]["values"].append(temp_la_list)

    return ret_map


def shutter_pic_data_assembly(vid, search_kw, pic_list):
    """
    过滤，组装 shutterstock 图片搜索页面的数据。返回数据类型为 dict
    {"thumb_list": [{"vid": vid,
                     "search_kw": search_kw,
                     "search_time": datetime.datetime.now(),
                     "pic_link": pic_list[0]['tu'],
                     "link_md5": link_md5,
                     "pic_height": pic_list[0]['th'],
                     "pic_weight": pic_list[0]['tw']}],
     "large_list": []
    }
    vid: str. chat-attraction table id
    search_kw: str. search key words
    pic_list: shutterstock pic spider return list data
    """
    search_time = time.strftime("%Y-%m-%d %H:%M:%S")

    ret_map = {"thumb": {"fields": ["vid", "search_kw", "search_time",
                                    "pic_link", "link_md5"],
                         "values": [],
                         "table": "attraction_shutter_thumb_pic"
                         },
               "large": {"fields": ["vid", "search_kw", "search_time",
                                    "pic_link", "link_md5"],
                         "values": [],
                         "table": "attraction_shutter_large_pic"}
               }
    for pic_meta in pic_list:
        tb_link = pic_meta.get('thumb_link')
        tb_link_md5 = get_md5(tb_link)
        temp_tb_list = [vid, search_kw, search_time, tb_link, tb_link_md5]
        ret_map["thumb"]["values"].append(temp_tb_list)

        large_link = pic_meta.get('large_link')
        large_link_md5 = get_md5(large_link)
        temp_la_list = [vid, search_kw, search_time,
                        large_link, large_link_md5]
        ret_map["large"]["values"].append(temp_la_list)

    return ret_map
