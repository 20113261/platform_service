#coding:utf-8
from mioji.spider_factory import factory
from mioji import spider_factory
from mioji.common.task_info import Task
from proj.my_lib.Common.Browser import proxy_pool

insert_db = None
get_proxy = proxy_pool.get_proxy
debug = False

source = 'bestwest'
spider_factory.config_spider(insert_db, get_proxy, debug, need_flip_limit=False)
old_spider_tag = source + 'ListHotel'
spider = factory.get_spider_by_old_source(old_spider_tag)
task = Task()
task.content = '&印度喀拉拉邦恰拉库德伊&20180525&2'
task.ticket_info = {'locationLng': '13.404954', 'locationLat': '52.5200066'}
spider.task = task
error_code = spider.crawl(required=required, cache_config=none_cache_config)
print(error_code)