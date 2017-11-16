from proj.celery import app

includes = ['proj.tasks',
            'proj.hotel_tasks',
            'proj.poi_pic_spider_tasks',
            'proj.qyer_city_spider',
            'proj.qyer_poi_tasks',
            'proj.tripadvisor_city_query_task',
            'proj.qyer_city_query_task',
            'proj.tripadvisor_city',
            'proj.hotel_list_task',
            'proj.qyer_attr_task',
            'proj.poi_nearby_city_task',
            'proj.daodao_img_rename_tasks'
            ]
if __name__ == '__main__':
    print app.control.rate_limit('proj.tasks.get_images', '60/s')
    # app.now()
    # print 'Hello World'
    # print 'Hello World'
    # for task_name in app.tasks.keys():
    #     if task_name.startswith('proj.'):
    #         print task_name
    #         app.control.rate_limit(task_name, '60/s')
            # print 'Hello World'

            # for task_name in app.tasks.keys():
            #     print task_name
            # if task_name.startswith('proj.'):
            #     print task_name
            # app.control.rate_limit('proj.tasks.get_images', '1/s')
