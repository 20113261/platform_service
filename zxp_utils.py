# -*- coding: utf-8 -*-
# @Time    : 2018/4/29
# @Author  : xiaopeng
# @Site    : boxueshuyuan
# @File    : zxp_utils.py
# @Software: PyCharm
import json
import requests

def get_zxp_proxy(*args, **kwargs):
    get_proxy = requests.get('http://10.10.239.46:8088/proxy').content
    content = json.loads(get_proxy)
    proxy = content['resp'][0]['ips'][0]['inner_ip']
    return str(proxy)

if __name__ == '__main__':
    print(get_zxp_proxy())