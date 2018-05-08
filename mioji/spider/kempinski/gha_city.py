# -*- coding: utf-8 -*-

import requests
import json
from lxml import etree
import re
def main():
    cityid = re.compile("\d+")

    host = 'https://zh.gha.com'
    url = "https://zh.gha.com/Destinations/Europe?viewMode=list"
    headers = {
        "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, "
                     "like Gecko) Chrome/64.0.3282.186 Safari/537.36",

    }
    l = []
    req = requests.get(url,headers=headers)
    selecet = etree.HTML(req.text)
    url_list = selecet.xpath("//div[@class='Filter Filter--destination Filter--primary2 Filter--typeSelect']/select/option/@data-url")
    for url_1 in url_list:
        req = requests.get(host+url_1, headers=headers)
        selecet_1 = etree.HTML(req.text)
        url_list_1 = selecet_1.xpath("//div[@class='DestinationsList DestinationsList--country u-isHidden-sm-down']/nav/a")
        country = []
        for item in url_list_1:
            module = item.xpath("./@luana-module")
            if module:
                country.append(item.xpath("./text()")[0])
                continue
            name = item.xpath("./text()")[0]
            href = item.xpath("./@href")[0]
            data = {
                "city":None,
                "country":name.strip().encode("utf-8"),
                "href":cityid.findall(href)[0]
            }
            l.append(data)
        url_list_2 = selecet_1.xpath("//div[@class='DestinationsList DestinationsList--country u-isHidden-sm-down']/nav/ul")
        for index,item_2 in enumerate(url_list_2):
            name = item_2.xpath("./li/a/text()")
            href = item_2.xpath("./li/a/@href")
            for i in range(len(name)):
                data = {
                    "city": name[i].strip().encode("utf-8"),
                    "country": country[index].strip().encode("utf-8"),
                    "href": cityid.findall(href[i])[0]
                }
                l.append(data)
    return {"gha":l}


if __name__ == '__main__':
    with open("city.json",'a') as w:
        w.write(json.dumps(main(),ensure_ascii=False))
