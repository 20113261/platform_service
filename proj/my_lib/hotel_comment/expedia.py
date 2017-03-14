# coding=utf-8
import json

from data_object import Review


def parser(content, url):
    flag = False
    hotel_reviews_json = json.loads(content)
    hotel_reviews_list = hotel_reviews_json.get("reviewDetails").get("reviewCollection").get("review")
    for hotel_reviews in hotel_reviews_list:

        r = Review('expedia')

        try:
            r.sid = hotel_reviews.get('hotelId').encode('utf-8')
            print 'sid', r.sid
        except Exception, e:
            print str(e)

        try:
            r.cid = hotel_reviews.get("reviewId").encode('utf-8')
            print 'cid', r.cid
        except Exception, e:
            print str(e)

        try:
            r.username = hotel_reviews.get("userNickname").encode('utf-8')
            print 'username', r.username
        except Exception, e:
            print str(e)

        try:
            r.rating = hotel_reviews.get("ratingOverall")
            print 'rating', r.rating
        except Exception, e:
            print str(e)

        try:
            r.date = hotel_reviews.get("reviewSubmissionTime").encode('utf-8').replace('Z', '').replace('T', ' ')
            print 'date', r.date
        except Exception, e:
            print str(e)

        try:
            r.language = hotel_reviews.get("contentLocale").encode('utf-8')
            print 'language', r.language
        except Exception, e:
            print str(e)

        try:
            r.title = hotel_reviews.get("title").encode('utf-8')
            print 'title', r.title
        except Exception, e:
            print str(e)
        try:
            r.comment = hotel_reviews.get("reviewText").encode('utf-8')
            print 'comment', r.comment
        except Exception, e:
            print str(e)
        print 'saved', r.save()
        flag = r.flag
    return flag


if __name__ == '__main__':
    import requests

    target_url = 'https://www.expedia.com/ugc/urs/api/hotelreviews/hotel/8210032/?_type=json&start=0&items=100000&sortBy=&categoryFilter=&languageFilter=&languageSort=en&expweb.activityId=f9158a1d-9d76      -4dbb-a2da-02d98ea79fcc&pageName=page.Hotels.Infosite.Information&orign=&caller=Expedia&_=1465961131865'
    target_url = 'https://www.expedia.cn/ugc/urs/api/hotelreviews/hotel/1699407/?_type=json&start=0&items=100000&sortBy=&categoryFilter=&languageFilter=&anguageSort=zh&expweb.activityId=eb481338-67ef-4b6c-a81f-9dd2f8edf957&pageName=page.Hotels.Infosite.Information&origin=&caller=Expedia&guid=1b1ae9827ce1495b8e3995fda9024720'
    headers = {
        'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36'
    }
    page = requests.get(target_url, headers=headers)
    page.encoding = 'utf8'
    print page.text

    parser(page.text, target_url)
