# coding=utf-8
import lxml.html as HTML

from data_object import Review


def parser(content, url):
    root = HTML.fromstring(content)

    count = 0
    flag = False
    for row in root.find_class('review_item'):
        print '------ count: %s --------' % count
        r = Review('booking')
        try:
            r.date = row.find_class('review_item_date')[0].text_content().strip().encode('utf-8')
        except:
            pass
        try:
            r.username = row.find_class('review_item_reviewer')[0].xpath('./h4/text()')[0].strip().encode('utf-8')
        except:
            pass
        try:
            r.language = row.find_class('reviewer_country')[0].text_content().strip().encode('utf-8')
        except:
            pass
        try:
            r.rating = row.find_class('review_item_review')[0].find_class('review_item_review_score')[
                0].text_content().strip().encode('utf-8')
        except:
            pass
        try:
            r.title = row.find_class('review_item_review')[0].find_class('review_item_header_content')[
                0].text_content().strip().encode('utf-8').replace('“', '').replace('”', '')
        except:
            pass
        try:
            review_negative = \
                row.find_class('review_item_review')[0].find_class('review_item_review_content')[0].find_class(
                    'review_neg')[0].text_content().encode('utf-8').replace('客人没有留下任何评语。', '').replace('\n',
                                                                                                       '').replace(
                    '\t', '').replace('눉', '').replace('눇', '').replace('\r', '').strip()
        except:
            review_negative = ''
        try:
            review_positive = \
                row.find_class('review_item_review')[0].find_class('review_item_review_content')[0].find_class(
                    'review_pos')[0].text_content().encode('utf-8').replace('客人没有留下任何评语。', '').replace('\n',
                                                                                                       '').replace(
                    '\t', '').replace('눉', '').replace('눇', '').replace('\r', '').strip()
        except:
            review_positive = ''
        comment = review_negative + ' ' + review_positive
        if len(comment.strip()) != 0:
            r.comment = comment.strip()

        try:
            item = row.find_class('review_item_review')[0].find_class('review-helpful__form')[0]
            sid = item.xpath('./input[1]/@value')[0]
            cid = item.xpath('./input[2]/@value')[0]
        except:
            sid = ''
            cid = ''
        r.sid = sid
        r.cid = cid
        if r.sid:
            print r.sid
            print r.cid
            print r.date
            print r.username, r.language
            print r.rating
            print r.title
            print len(r.comment)
            print r.comment
            print r.save()
            flag = True
        count += 1
    return flag


if __name__ == '__main__':
    import requests

    target_url = 'http://www.booking.com/reviewlist.zh-cn.html?pagename=landmark-suites;cc1=ke;type=total;dist=1;offsets=200;rows=100;'
    target_url = 'http://www.booking.com/reviewlist.zh-cn.html?label=gen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBA-gBAagCBA;sid=04bb4f5be7caced0d2801004dd9e9bec;pagename=la-goleta-de-mar-adults-only;cc1=es;type=total;score=;dist=1;rows=100;r_lang=en;'
    target_url = 'http://www.booking.com/reviewlist.zh-cn.html?pagename=la-goleta-de-mar-adults-only;cc1=es;type=total;score=;dist=1;offsets=200;rows=100;'
    headers = {
        'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36'
    }
    page = requests.get(target_url, headers=headers)
    page.encoding = 'utf8'
    parser(page.text, target_url)
