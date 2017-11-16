#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/17 下午9:09
# @Author  : Hou Rong
# @Site    : 
# @File    : elong_test.py
# @Software: PyCharm
from proj.my_lib.new_hotel_parser import elong_parser

# def test_elong_parser(page):
#     return elong_parser(page,
#                         url='',
#                         other_info={'source_id': 'test', 'city_id': 'test'}
#                         )

import unittest
import json
from proj.my_lib.new_hotel_parser.expedia_parser import expedia_parser
from mioji.common.ufile_handler import download_file


def test_expedia_parser(page):
    return expedia_parser(page,
                          url='',
                          other_info={'source_id': 'test', 'city_id': 'test'}
                          )


if __name__ == '__main__':
    from proj.my_lib.Common.Browser import MySession

    # with MySession(need_cache=True, do_not_delete_cache=True) as session:
    #     # page = session.get('http://ihotel.elong.com/367231/')
    #     page = session.get(
    #         "https://travelads.hlserve.com/TravelAdsService/v3/Hotels/TravelAdClickRedirect?trackingData=Cmp-qkAgxmJOYm3EzMgli6W1uYDrDONSGmmuhJ+JJIAZphECvanJ9QdBNDRq2bBTxmzpCQgZ61vjdI97TvOFxzcEevo3KjcfCEdJzwaAxHOdfQ2ibtCnTNRfS3CI9SctR1hLX6515APgwK+1pxmwEStGPZMCqHRsgOvXpeSQss1jeJMoBOwd5yr9F/lYrUeW3p+bYahEaLARDiijVSUc6qUBfkRfAz5R8ky1r+TQCyh0Q4uDylvrDIqwD5BAtzlBH8fQZZ+9s1fONTUO1OdfIs5Z3Te2T8078mE5IpMazirh7WCpNez2P2UXHBVeTOIExxT+NsSwC/9Y0RcJXtnv+oS6RgAYO1tH70da+iFHtQYQ6tZ6OPaGR84S6TEtXg8q2vNn3P+NUj2umpZL1JcAGHLeIaGUQ22EmwJWlXjdA2L7paS4a2CyeRZkvXrfF1kZCZs82BGpucg37z9l2aycyk+LOdqgoKzg+AFrfXJMunTU8/720Jp6j/m5TkEMpNulEmrhl2Epv4kp6AarikadjbvofIbKVHg2HqfFPnO4+8Pra2d2yrMdHb9ZNky8mh/iYtWVCI97WSS+RBLr/wa8S80NLwHjdUbe1pLpc5/kCeaZCcalcO9Z5Sh9GdvcWjCyvezxIr0YMyaIF5EqHUnRxPctqa4o+OjVhSCyfL4XpauIc562JzbZI5IS00h1IFCMN1KlOjMi4599/cJp65M9hdnMSOm0nCzL+fIVd2lB467ykPG19+sU25coUX4WvDP75pgiMFxzkLy6MfL+9W0wWFU8OBXysHZyMHZavJA5jsa0ICRMwU0kQTUKNBnPH9b8QNbQOuaSalhc1bvENaiQpn0pwuwRy5LocusjzJVGS3bzjBBw+WgNDTPGkbqaLClbw5UkIvagbvhQJWQ1v3cT2A8DTf5x7d5KtSRZvjdVsLQcUfRU6jkLUdORKmVwxDR1lZCUjg0dqm2mcxqn+l5Wc0x7ie8xNFLXCubsEOeMNYmzdnSLtIgt+OkiGN5nD7ulLFKFfAXdYvTVNK2m09v66IdnoD5fH6SMkg5BoCfB/jhyXZnYpSmooY8E7TFHzRJS+30quP+S6HmHoEMhghpLeUuVgmu138baTTWuONXFwlMj5cM=&rank=3&testVersionOverride=11141.44405.1%2C13487.51625.0%2C14567.99990.0&destinationUrl=https%3A%2F%2Fwww.expedia.com.hk%2FHotels-Hilton-Los-Angeles-Airport.h5907.Hotel-Information&candidateHmGuid=68f748cb-cd7c-47ac-a90c-7dbed2aeed15&beaconIssued=2017-10-02T06:12:45")
    # result = page.text
    # print(page.text)
    # test_expedia_parser(page.text)

    with MySession(need_proxies=True) as session:
        page = session.get(
            "https://travelads.hlserve.com/TravelAdsService/v3/Hotels/TravelAdClickRedirect?trackingData=Cmp-qkAgxmJOYm3EzMgli6W1uYDrDONSGmmuhJ+JJIAZphECvanJ9QdBNDRq2bBTxmzpCQgZ61vjdI97TvOFxzcEevo3KjcfCEdJzwaAxHOdfQ2ibtCnTNRfS3CI9SctR1hLX6515APgwK+1pxmwEStGPZMCqHRsgOvXpeSQss1jeJMoBOwd5yr9F/lYrUeW3p+bYahEaLARDiijVSUc6qUBfkRfAz5R8ky1r+TQCyh0Q4uDylvrDIqwD5BAtzlBH8fQZZ+9s1fONTUO1OdfIs5Z3Te2T8078mE5IpMazirh7WCpNez2P2UXHBVeTOIExxT+NsSwC/9Y0RcJXtnv+oS6RgAYO1tH70da+iFHtQYQ6tZ6OPaGR84S6TEtXg8q2vNn3P+NUj2umpZL1JcAGHLeIaGUQ22EmwJWlXjdA2L7paS4a2CyeRZkvXrfF1kZCZs82BGpucg37z9l2aycyk+LOdqgoKzg+AFrfXJMunTU8/720Jp6j/m5TkEMpNulEmrhl2Epv4kp6AarikadjbvofIbKVHg2HqfFPnO4+8Pra2d2yrMdHb9ZNky8mh/iYtWVCI97WSS+RBLr/wa8S80NLwHjdUbe1pLpc5/kCeaZCcalcO9Z5Sh9GdvcWjCyvezxIr0YMyaIF5EqHUnRxPctqa4o+OjVhSCyfL4XpauIc562JzbZI5IS00h1IFCMN1KlOjMi4599/cJp65M9hdnMSOm0nCzL+fIVd2lB467ykPG19+sU25coUX4WvDP75pgiMFxzkLy6MfL+9W0wWFU8OBXysHZyMHZavJA5jsa0ICRMwU0kQTUKNBnPH9b8QNbQOuaSalhc1bvENaiQpn0pwuwRy5LocusjzJVGS3bzjBBw+WgNDTPGkbqaLClbw5UkIvagbvhQJWQ1v3cT2A8DTf5x7d5KtSRZvjdVsLQcUfRU6jkLUdORKmVwxDR1lZCUjg0dqm2mcxqn+l5Wc0x7ie8xNFLXCubsEOeMNYmzdnSLtIgt+OkiGN5nD7ulLFKFfAXdYvTVNK2m09v66IdnoD5fH6SMkg5BoCfB/jhyXZnYpSmooY8E7TFHzRJS+30quP+S6HmHoEMhghpLeUuVgmu138baTTWuONXFwlMj5cM=&rank=3&testVersionOverride=11141.44405.1%2C13487.51625.0%2C14567.99990.0&destinationUrl=https%3A%2F%2Fwww.expedia.com.hk%2FHotels-Hilton-Los-Angeles-Airport.h5907.Hotel-Information&candidateHmGuid=68f748cb-cd7c-47ac-a90c-7dbed2aeed15&beaconIssued=2017-10-02T06:12:45")

    print(page.text)
