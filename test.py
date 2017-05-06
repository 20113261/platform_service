# from proj.celery import app
#
# @app.task(bind=True)
# def abc(self):
#     print 'Hello World'
#
# abc()

from proj.hotel_list_task import hotel_list_database

if __name__ == '__main__':
    print hotel_list_database('agoda', u'11217')
