#coding:utf-8
# @Time    : 2018/4/30
# @Author  : xiaopeng
# @Site    : boxueshuyuan
# @File    : test_request.py
# @Software: PyCharm

import requests

url = "https://www.bestwestern.net.cn/booking-path/searchhotel"

headers = {
    'Cookie': 'search_numberOfRooms=1;search_checkInDate=2018-05-01; search_checkOutDate=2018-05-03;search_numAdults=1%2C1%2C1; search_numChild=0%2C0%2C0;search_destination=%E5%8D%B0%E5%BA%A6%E5%96%80%E6%8B%89%E6%8B%89%E9%82%A6%E6%81%B0%E6%8B%89%E5%BA%93%E5%BE%B7%E4%BC%8A;search_locationLat=52.5200066; search_locationLng=13.404954;'
    }

response = requests.request("GET", url, headers=headers)

print(response.text)