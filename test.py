# from proj.celery import app
#
# @app.task(bind=True)
# def abc(self):
#     print 'Hello World'
#
# abc()

from SDK.HotelListSDK import hotel_list_database

if __name__ == '__main__':
    print hotel_list_database('agoda', u'11217')
