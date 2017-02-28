from proj.hotel_tasks import hotel_base_data
from proj.my_lib.task_module.task_func import get_task_total
from proj.poi_pic_spider_tasks import google_spider, shutter_spider, flickr_spider
from proj.qyer_city_query_task import qyer_city_query_task
from proj.qyer_city_spider import qyer_country_spider
from proj.tasks import get_comment
from proj.tasks import get_images
from proj.tasks import venere_comment, booking_comment, expedia_comment
from proj.tripadvisor_city_query_task import tripadvisor_city_query_task
from proj.hotel_list_task import hotel_list_task
from proj.tasks import craw_html
from proj.qyer_poi_tasks import qyer_poi_task
from proj.tasks import get_lost_attr, get_lost_rest_new, get_lost_shop
from proj.tasks import get_hotel_images_info
from proj.poi_nearby_city_task import poi_nearby_city_task
from proj.tasks import get_daodao_image_url
from proj.daodao_img_rename_tasks import daodao_img_rename_task


def add_target(task_url, miaoji_id, special_str, **kwargs):
    res1 = get_comment.delay(task_url, 'zhCN', miaoji_id, special_str, **kwargs)
    res2 = get_comment.delay(task_url, 'en', miaoji_id, special_str, **kwargs)
    return res1, res2


if __name__ == '__main__':
    _count = 0
    for task_id, args, worker in get_task_total(limit=100000):
        # todo get_comment With Task
        if worker == 'poi_comment':
            add_target(args['url'], args['mid'], args['special_str'], task_id=task_id)
            _count += 1

        # todo hotel list init by Task
        if worker == 'hotel_list':
            hotel_list_task.delay(args['source'], args['city_id'], args['part'], task_id=task_id)
            _count += 1

        # todo hotel base data init by Task
        if worker == 'hotel_base_data':
            hotel_base_data.delay(args['source'], args['hotel_url'], args['other_info'], args['part'], task_id=task_id)
            _count += 1

        # todo get img by Task
        if worker == 'img_task':
            get_images.delay(args['source'], args['target_url'], task_id=task_id)
            _count += 1

        # todo poi_pic_list by Task
        if worker == 'poi_pic_task':
            if args['source'] == 'google':
                google_spider.delay(args['mid'], args['keyword'], task_id=task_id)
                _count += 1
            elif args['source'] == 'shutter':
                shutter_spider.delay(args['mid'], args['keyword'], task_id=task_id)
                _count += 1
            elif args['source'] == 'flickr':
                flickr_spider.delay(args['mid'], args['keyword'], task_id=task_id)
                _count += 1

        if worker == 'hotel_comment':
            _count += 1
            if args['source'] == 'booking':
                booking_comment.delay(args['target_url'], task_id=task_id)
            elif args['source'] == 'expedia':
                expedia_comment.delay(args['target_url'], task_id=task_id)
            elif args['source'] == 'venere':
                venere_comment.delay(args['target_url'], task_id=task_id)

        # # todo qyer city by Task
        # if worker == 'qyer_city':
        #     qyer_spider.delay(args['continent'], args['country'], task_id=task_id)

        # todo tp city query by Task
        if worker == 'tp_city_query_task':
            _count += 1
            tripadvisor_city_query_task.delay(args['city_name'], task_id=task_id)

        # todo qyer city query by Task
        if worker == 'qyer_city_query_task':
            _count += 1
            qyer_city_query_task.delay(args['city_name'], task_id=task_id)

        # todo qyer country task
        if worker == 'qyer_country_task':
            _count += 1
            qyer_country_spider.delay(args['country_id'], args['country_link'], task_id=task_id)

        # todo google drive task
        if worker == 'google_drive_task':
            _count += 1
            craw_html.delay(args['url'], args['flag'], args['table_name'], task_id=task_id)

        # todo qyer poi task
        if worker == 'qyer_poi_task':
            _count += 1
            qyer_poi_task.delay(args['target_url'], args['city_id'], task_id=task_id)

        # todo daodao poi base data
        if worker == 'daodao_poi_base_data':
            if args[u'type'] == u'attr':
                get_lost_attr.delay(args['target_url'], args['city_id'], task_id=task_id)
                _count += 1
            if args[u'type'] == u'rest':
                get_lost_rest_new.delay(args['target_url'], args['city_id'], task_id=task_id)
                _count += 1
            if args[u'type'] == u'shop':
                get_lost_shop.delay(args['target_url'], args['city_id'], task_id=task_id)
                _count += 1

        # todo hotel image info
        if worker == 'hotel_image_info_task':
            get_hotel_images_info.delay(args['path'], args['part'], args['desc_path'], task_id=task_id)
            _count += 1

        # todo poi nearby city task
        if worker == 'poi_nearby_city_task':
            poi_nearby_city_task.delay(poi_id=args['mid'], poi_city_id=args['city_id'], poi_map_info=args['map_info'],
                                       task_id=task_id)
            _count += 1

        if worker == 'daodao_img_url_task':
            get_daodao_image_url.delay(args['source_url'], args['mid'], task_id=task_id)
            _count += 1

        # todo daodao img rename task
        if worker == 'daodao_img_rename_task':
            daodao_img_rename_task.delay(args['file_name'], args['src_path'], args['dst_path'], args['bucket_name'],
                                         args['img_url'], args['mid'], args['table_name'], task_id=task_id)
            _count += 1

    print _count
