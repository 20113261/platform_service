import re
import lxml.html as HTML

from data_object import Review

pattern = re.compile('hotelId=(\d+)')


def parser(content, url):
    flag = False
    source_id = pattern.findall(url)[0]
    root = HTML.fromstring(content)

    reviews = root.xpath('//div [@id="guest-reviews"]')[0]
    guest_reviews = reviews.xpath('//div [@class="reviews-list"]')
    for each_list in guest_reviews:
        review_list = each_list.xpath('//div [@class="review-card clearfix"]')
        for each_review in review_list:
            r = Review('venere')
            r.sid = source_id
            print 'sid', r.sid
            try:
                times = each_review.xpath('./div[@class="review-card-meta"]//span[@class="date"]/text()')[0].encode(
                    'utf-8').strip()  # float(each_review.xpath('./@data-review-date')[0].encode('utf-8')[:-3])
                # x = time.localtime(times)
                # r.date = time.strftime('%Y-%m-%d %H:%M:%S', x)
                r.date = times
                print 'reviews_time', r.date
            except Exception, e:
                print str(e)

            try:
                r.rating = each_review.xpath('.//div[@class="review-score"]/span/strong/text()')[0].encode(
                    'utf-8').strip()  # str(each_review.xpath('./@data-review-rating')[0].encode('utf-8'))
                print 'rating', r.rating
            except Exception, e:
                print str(e)

            try:
                r.title = each_review.find_class('review-summary')[0].text_content().encode('utf-8').strip()
                print 'title', r.title
            except Exception, e:
                print str(e)

            try:
                r.comment = each_review.find_class('review-content')[0].find_class('expandable-content')[
                    0].text_content().encode('utf-8').strip().replace(
                    '\n', '')
                print 'comment', r.comment
            except Exception, e:
                print str(e)

            try:
                r.username = each_review.find_class('review-card-meta-reviewer')[0].xpath('./text()')[0].encode('utf-8')
                print 'user_name', r.username
            except Exception, e:
                print str(e)

            try:
                r.language = each_review.find_class('locality')[0].text_content().encode('utf-8')
                print 'language', r.language
            except Exception, e:
                print str(e)

            print 'saved', r.save()
            flag = r.flag
    return flag


if __name__ == '__main__':
    import requests

    target_url = 'http://zh.venere.com/hotel/details.html?roomno=1&rooms%5B0%5D.numberOfAdults=2&hotelId=471873&display=reviews'
    headers = {
        'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36'
    }
    page = requests.get(target_url, headers=headers)
    page.encoding = 'utf8'
    parser(page.text, target_url)
