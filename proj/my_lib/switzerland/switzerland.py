# coding=utf-8
import db_localhost
import requests
from common.common import get_proxy
from lxml import html
from lxml.html import tostring

headers = {
    'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36'
}


def update_db(args):
    # (introduction1, introduction2, email, website, image_list, contact_info)
    sql = 'update switzerland set introduction1=%s,introduction2=%s,email=%s,site=%s,image_list=%s,contact_info=%s where id=%s and type=%s'
    return db_localhost.ExecuteSQL(sql, args)


def switzerland_parser(target_url, m_id, m_type):
    # PROXY = get_proxy(source="Platform")
    # proxies = {
    #     "http": "http://" + PROXY,
    # }
    page = requests.get(target_url, headers=headers, timeout=120)
    page.encoding = 'utf8'
    content = page.text
    root = html.fromstring(content)
    try:
        introduction1 = root.find_class('lead')[0].text
    except:
        introduction1 = ''

    try:
        introduction2 = root.get_element_by_id('col_main').text
    except:
        introduction2 = ''

    try:
        image_list = '|'.join(root.xpath('//*[@id="fotos"]//img/@src'))
    except:
        image_list = ''

    contact_node = ''

    for node in root.find_class('box toggleable'):
        for node_title in node.xpath('descendant::span'):
            if node_title.text == u'联系':
                contact_node = node
                break

    email = ''
    website = ''
    contact_info = ''
    if contact_node:
        try:
            for url in contact_node.find_class('box_content')[0].xpath('a/@href'):
                if 'mailto' in url:
                    email = url.split('mailto:')[1]
                if '://' in url:
                    website = url.split('://')[1]
        except:
            pass

        text_list = []
        text_list.append(contact_node.find_class('box_content')[0].text.strip())

        for text_node in contact_node.find_class('box_content')[0].getchildren():
            line_text = tostring(text_node)
            if '<br>' in line_text:
                result_text = line_text.replace('<br>', '')
                if result_text:
                    text_list.append(result_text.strip())
        contact_info = '|_|'.join(text_list)

    data = (introduction1, introduction2, email, website, image_list, contact_info, m_id, m_type)
    return data


def get_task():
    sql = 'select url,id,type from switzerland where introduction1="" and introduction2="" and image_list="" and contact_info=""'
    for line in db_localhost.QueryBySQL(sql):
        yield line['url'], line['id'], line['type']


if __name__ == '__main__':
    # target_url = 'http://www.myswitzerland.com//zh-cn/suggestions/grand-tour-of-switzerland/experiences-along-the-grand-tour/geschichte/sion-old-town.html'
    # m_id = 'page-36241'
    # m_type = 'summer'
    count = 0
    for target_url, m_id, m_type in get_task():
        data = switzerland_parser(target_url, m_id, m_type)
        count += 1
        print target_url
        print update_db(data)
        print count
