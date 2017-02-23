# coding=utf-8
import pymysql
import re
from lxml import html


def parse(content, url, language, miaoji_id, special_str):
    root = html.fromstring(content)
    data_list = []

    # 评论详情
    comments = len(root.find_class('reviewSelector'))
    if comments == 0:
        return data_list
    print '******* reviews *******'
    long_count = 0
    count = 1
    for rev in root.find_class('reviewSelector'):
        print '---- %s ---' % count
        review_url = ''
        review_id = ''
        review_title = ''
        review_text = ''
        review_date = ''
        review_grade = ''
        review_user = ''
        try:
            is_more_text = len(rev.find_class('partial_entry')[0].find_class('partnerRvw'))
            review_url = 'http://www.tripadvisor.cn' + \
                         rev.find_class('quote')[0].xpath('a/@href')[0].strip().encode('utf-8').split('#')[0]
            review_id = re.compile(r'-r(\d+)').findall(review_url)[0]
            review_city_id = re.compile(r'-g(\d+)').findall(review_url)[0]
            review_attr_id = re.compile(r'-d(\d+)').findall(review_url)[0]

            if is_more_text == 0:
                # 短评论
                short_data = short_comment_parse(rev, review_url, miaoji_id, url, language)
                data_list.append(short_data)
            else:
                # 长评论
                long_comment_url = 'http://www.tripadvisor.cn/ExpandedUserReviews-g%s-d%s?target=%s&context=1&reviews=%s&servlet=Restaurant_Review&expand=1' % (
                    review_city_id, review_attr_id, review_id, review_id)
                print 'long_comment_url:   %s' % long_comment_url
                long_count += 1
                print 'insert long:', \
                    insert_long((long_comment_url.strip(), language, miaoji_id), 'tp_comment_long_' + special_str)
        except Exception, e:
            print 'comment parse error:'
            print str(e)
        count += 1
    if len(data_list) != 0:
        print 'insert comment', insert_db(data_list, 'tp_comment_' + special_str), url
    else:
        print 'no comment', url

    return len(data_list) + long_count


def short_comment_parse(rev, review_url, miaoji_id, url, language):
    source = 'tripadvisor'
    review_id = re.compile(r'-r(\d+)').findall(review_url)[0]
    review_city_id = re.compile(r'-g(\d+)').findall(review_url)[0]
    review_attr_id = re.compile(r'-d(\d+)').findall(review_url)[0]

    try:
        review_title = rev.find_class('noQuotes')[0].text.strip().encode('utf-8')
    except:
        review_title = ''

    try:
        review_text = rev.find_class('partial_entry')[0].text.strip().encode('utf-8').strip()
    except:
        review_text = ''

    try:
        review_date = '-'.join(re.compile(r'(\d+)').findall(rev.find_class('ratingDate')[0].text.encode('utf-8')))
        if len(review_date) < 2:
            review_date = rev.find_class('ratingDate')[0].xpath('@title')[0].encode('utf-8')
    except Exception, e:
        review_date = ''

    try:
        grade = '-1'
        review_grade = '-1'
        grade = rev.find_class('rate sprite-rating_s rating_s')[0].xpath('img/@alt')[0].strip().encode('utf-8')
        grade_num = re.compile(r'(\d+)').findall(grade)
        if len(grade_num) > 1:
            review_grade = grade_num[0] + '.' + grade_num[1]
        else:
            review_grade = grade_num[0]
    except:
        grade = '-1'
        review_grade = '-1'

    review_user = ''
    try:
        review_user = rev.find_class('expand_inline scrname mbrName_')[0].text.strip().encode('utf-8')
    except:
        try:
            review_user = rev.find_class('expand_inline scrname')[0].text.strip().encode('utf-8')
        except:
            pass

    try:
        user_link = \
            re.compile(r'window.open\(\'(.*)\'\)').findall(rev.find_class('memberBadging')[0].xpath('div/@onclick')[0])[
                0].strip().encode('utf-8')
    except:
        user_link = ''
    if user_link.find('http://www.tripadvisor') > -1:
        pass
    else:
        if user_link:
            user_link = 'http://www.tripadvisor.cn' + user_link

    print 'review_city_id: %s' % review_city_id
    print 'review_attr_id: %s' % review_attr_id
    print 'review_url: %s' % review_url
    print 'review_id: %s' % review_id
    print 'review_title: %s' % review_title
    print 'review_text: %s' % review_text
    print 'review_date: %s' % review_date
    print 'review_grade: %s' % review_grade
    print 'review_user: %s' % review_user
    print 'user_link: %s' % user_link
    data = (
        source, review_city_id, review_attr_id, review_id, review_title, review_text, review_url, review_date,
        review_grade,
        review_user, user_link, url, miaoji_id, language)
    return data


def long_comment_parse(content, url, language, miaoji_id='NULL'):
    rev = html.fromstring(content.decode('utf-8').encode('utf-8'))
    source = 'tripadvisor'
    review_id = re.compile(r'target=(\d+)').findall(url)[0]
    city_id = re.compile(r'-g(\d+)').findall(url)[0]
    attr_id = re.compile(r'-d(\d+)').findall(url)[0]
    review_url = 'http://www.tripadvisor.cn/ShowUserReviews-g%s-d%s-r%s.html' % (city_id, attr_id, review_id)
    print review_id, city_id

    title = rev.find_class('noQuotes')[0].text.strip().encode('utf-8')
    comment = rev.find_class('entry')[0].xpath('p/text()')[0].strip().encode('utf-8')
    try:
        date = rev.xpath('//*[@class="ratingDate relativeDate"]/@title')[0]
    except Exception, e:
        date_str = rev.xpath('//*[@class="ratingDate"]/text()')[0].strip().encode('utf-8')
        date = '-'.join(re.compile(r'(\d+)').findall(date_str))
    grade = float('.'.join(
        re.compile(r'(\d+)').findall(rev.xpath('//*[@class="rate sprite-rating_s rating_s"]/img/@class')[0])[0]))
    try:
        user = rev.xpath('//*[@class="username mo"]/span/text()')[0].strip().encode('utf-8')
    except:
        user = ''
    try:
        user_link = re.compile(r'window.open\(\'(.*)\'\)').findall(
            rev.xpath('//*[@class="totalReviewBadge badge no_cpu"]/@onclick')[0])[0].strip().encode('utf-8')
    except:
        user_link = ''
    if user_link.find('http://www.tripadvisor') > -1:
        pass
    else:
        if user_link:
            user_link = 'http://www.tripadvisor.cn' + user_link
    print 'city_id: %s' % city_id
    print 'attr_id: %s' % attr_id
    print 'review_url: %s' % review_url
    print 'review_id: %s' % review_id
    print 'title: %s' % title
    print 'comment:       %s' % comment
    print 'date: %s' % date
    print 'grade: %s' % grade
    print 'user: %s' % user
    print 'user_link: %s' % user_link
    data = (
        source, city_id, attr_id, review_id, title, comment, review_url, date, grade, user, user_link, url, miaoji_id,
        language)
    return data


def insert_db(args, table_name):
    conn = pymysql.connect(host='10.10.180.145', user='hourong', passwd='hourong', charset='utf8', db='Comment')
    with conn as cursor:
        sql = 'replace into {0} (source, source_city_id, source_id, review_id, review_title, review_text, review_link, comment_time, comment_rating, user_name, user_link, review_from, miaoji_id, language) values(%s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s)'.format(
            table_name)
        res = cursor.executemany(sql, args)
    conn.close()
    return res


def insert_long(args, table_name):
    conn = pymysql.connect(host='10.10.180.145', user='hourong', passwd='hourong', charset='utf8', db='Comment')
    with conn as cursor:
        sql = 'replace into {0} (`url`,`language`,`miaoji_id`) values(%s, %s, %s)'.format(table_name)
        res = cursor.executemany(sql, args)
    conn.close()
    return res
