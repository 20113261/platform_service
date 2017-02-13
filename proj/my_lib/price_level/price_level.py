# coding=utf-8
import db_localhost
import requests
from lxml import html


def get_yelp_price_level(page):
    page.encoding = 'utf8'
    content = page.text
    root = html.fromstring(content)
    try:
        price_level = root.find_class('price-range')[0].text.strip().replace('$', '¥')
    except Exception as e:
        price_level = ''
    return price_level


def get_daodao_price_level(page):
    page.encoding = 'utf8'
    root = html.fromstring(page.text)
    try:
        price_level = root.find_class('price_rating')[0].text.strip()
    except:
        price_level = ""
    return price_level


def update_db(args):
    sql = 'update price_level.chat_restaurant set price_level=%s where id=%s'
    return db_localhost.ExecuteSQL(sql, args)


if __name__ == '__main__':
    # yelp

    # target_url = 'https://www.yelp.com/biz/honeys-restaurant-san-jose-2'
    # target_url = 'https://www.yelp.com/biz/teotihuacan-mexican-caf%C3%A9-houston-3'
    # m_id = 'r0684377'
    # target_url = 'http://www.yelp.com/biz/menomale-pizza-napoletana-washington'
    # page = requests.get(target_url)
    # price_level = get_yelp_price_level(page)
    # print price_level
    # print 'Hello World'

    # daodao

    target_url = 'http://www.tripadvisor.cn/Restaurant_Review-g187269-d8753859-Reviews-Le_Verre_Galant-Saint_Etienne_Loire_Rhone_Alpes.html'
    m_id = 'r1075954'
    page = requests.get(target_url)
    price_level = get_daodao_price_level(page)
    print update_db((price_level, m_id))
