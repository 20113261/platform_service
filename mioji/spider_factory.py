#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Created on 2016年12月19日

@author: dujun
"""

import traceback
import importlib
import pkgutil
import os
from mioji.common.spider import Spider
import inspect
from mioji.common import spider, task_info
from mioji.common.utils import simple_get_http_proxy
from mioji.common.logger import logger


def config_spider(insert_db, get_proxy, debug=False, need_flip_limit=True, is_service_platform=False):
    """
    :param insert_db: 为原框架 common.insert_db 引用
    :param get_proxy: 获取代理方法 like get_proxy(source,a=None,b='ss')， 原框架 common.common get_proxy 方法引用 或 其他获取代理方法 
    :param debug: True/Flase 是否debug
    :param need_flip_limit: 是否限定翻页
    """
    spider.debug = debug
    spider.insert_db = insert_db
    spider.is_service_platform = is_service_platform
    if debug and not get_proxy:
        spider.slave_get_proxy = simple_get_http_proxy
    
    spider.NEED_FLIP_LIMIT = need_flip_limit

    spider.slave_get_proxy = get_proxy


class SpiderFactory(object):
    """
    :note:  抓取之前请设置 mioji.common.spider.insert_db 和 mioji.common.spider.get_proxy
    :see: get_spider
    :see: get_spider_by_targets
    :see: get_spider_by_old_source
    """

    def __init__(self):
        """
        Constructor
        """
        self.__spider_list = {}
        self.__old_source_spider = {}
        self.__load()

    def all(self):
        return self.__spider_list

    def __load(self):
        logger.debug('=======spider init start======')
        spider_list = {}
        old_source_spider = {}

        isReload = False
        if self.__spider_list:
            isReload = True

        source_module_names = find_module_names('spider', isReload=isReload)
        for source in source_module_names:
            logger.info("找到source：%s", source)
            spider_list[source] = {}
            spider_module_name = 'spider.' + source

            spider_module_names = find_module_names(spider_module_name, isReload=isReload)
            for spider_module in spider_module_names:
                try:
                    logger.info("找到module: %s", spider_module)
                    if spider_module.endswith('_spider'):
                        # 一个py脚本文件只应该有一个爬虫
                        desc, old_tag = init_spider(spider_module_name + '.' + spider_module, isReload=isReload)
                        if desc:
                            spider_list[source][desc[0]['source_type']] = desc[0]

                        if old_tag:
                            for k, v in old_tag[0].items():
                                old_source_spider[k] = v
                except Exception:
                    logger.info("寻找并加载 [ module ]: {0} 时出现异常，[ {1} ]".format(spider_module, traceback.format_exc()))

        self.__spider_list = spider_list
        self.__old_source_spider = old_source_spider

        logger.debug('spiders: %s', self.__spider_list)
        logger.debug('old source-spiders: %s', self.__old_source_spider)
        logger.debug('=======spider init complete======')

    def get_spider(self, source_name, source_type, required_targets=None):
        """
        通过 源;抓取类型;[目标类型]获取爬虫
        :param source_name: 源名称，不包含抓取目标。如 booking, ctrip
        :param source_type: 抓取目标
        :param required_targets: 目标类型,list。None or [] 不指定
        """
        spider = self.__spider_list.get(source_name, {}).get(source_type, None)
        if not spider:
            logger.info('can not find spider for source: %s', source_name)
            return None
        if not required_targets:
            return spider.get('spider_class')()

        un_support_targets = set(required_targets) - set(spider.get('targets'))
        if un_support_targets:
            logger.info('spider[%s] nonsupport targets: %s', spider.get('spider_class'), un_support_targets)
            return None
        else:
            return spider.get('spider_class')()

    def get_spider_by_targets(self, source_name, required_targets):
        """
        通过 源;目标类型 获取爬虫
        :param source_name: 源名称，不包含抓取目标。如 booking, ctrip
        :param required_targets: 目标类型,list。必须指定
        """
        if not source_name or not required_targets:
            return None

        source_spider = self.__spider_list.get(source_name, required_targets)
        if not source_spider:
            logger.info('can not find spider for source: %s', source_name)
            return None
        spider = self.__find_spider(source_spider, required_targets)
        return spider

    def get_spider_by_old_source(self, source):
        """
        通过老的源名获取爬虫
        :param source: 如 bookingList
        """
        spider_d = self.__old_source_spider.get(source, None)
        if not spider_d:
            return None
        spider = spider_d['spider_class']()
        spider.targets_required = spider_d['required']
        return spider

    def get_spider_by_old_task(self, task):
        """
        通过老的任务获得并初始化爬虫
        :param task: 任务
        :return: None 或已实例化后的爬虫
        """
        try:
            spider_d = self.__old_source_spider.get(task.source, None)
            if not spider_d:
                return None
            spider = spider_d['spider_class'](task)
            spider.targets_required = spider_d['required']
            return spider
        except Exception:
            return None

    def __find_spider(self, source_spider, required_targets):
        for _, spider in source_spider.items():
            un_support_targets = set(required_targets) - set(spider.get('targets'))
            if un_support_targets:
                continue
            else:
                return spider.get('spider_class')()

    def reload(self):
        """
        TODO
        """
        self.__load()
        return self.all()


def find_module_names(name='spider', isReload=False):
    p = importlib.import_module('.' + name, 'mioji')
    if isReload:
        reload(p)
        p = importlib.import_module('.' + name, 'mioji')

    return [name for _, name, _ in pkgutil.iter_modules([os.path.dirname(p.__file__)])]


def init_spider(module_name, isReload=False):
    """
    :param module_name: like  spider.booking.hotel_list_spider
    :return: 理论上只有一个spider 
    """
    spider_module = importlib.import_module('.' + module_name, 'mioji')
    if isReload:
        reload(spider_module)
        #         pydevd_reload.xreload(spider_module)
        spider_module = importlib.import_module('.' + module_name, 'mioji')

    spider_list = []
    old_source_spider = []
    for attr in inspect.getmembers(spider_module):
        if inspect.isclass(attr[1]) and attr[1].__module__.endswith('_spider') and attr[1].__module__.endswith(
                module_name):
            if issubclass(attr[1].__bases__[0], Spider) and not attr[1].unable:
                # 当为 Spider 子类或同类时加载
                try:
                    spider_clazz = getattr(spider_module, attr[0])
                    spider = spider_clazz()
                    if isinstance(spider, Spider):
                        spider_desc = {}
                        spider_desc['source_type'] = spider.source_type
                        spider_desc['spider_class'] = spider_clazz
                        spider_desc['targets'] = spider.targets.keys()
                        spider_list.append(spider_desc)

                        tag = {}
                        for k, v in spider.old_spider_tag.items():
                            tag[k] = v
                            v['spider_class'] = spider_clazz
                        old_source_spider.append(tag)

                except:
                    logger.exception('instance spider[%s]', attr[1])

    return spider_list, old_source_spider


factory = SpiderFactory()


def create_task_info(source, content=None, extra={}):
    task = task_info.Task(source)
    task.content = content
    task.extra = extra
    return task


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import common.insert_db
    from common.common import get_proxy
    from mioji import spider_factory
    from mioji.spider_factory import factory

    insert_db = common.insert_db
    get_proxy = get_proxy
    debug = False
    print "spider——adapter  " * 20
    spider_factory.config_spider(insert_db, get_proxy, debug, is_service_platform=True)

    task = Task()
    li = ['OKA&ASB&20170720', 'LXR&LBV&20170510', 'CHI&GUM&20170520', 'MMK&AKL&20170510']
    # task.content = "KIX&XIY&20170910"
    # task.source = 'pricelineFlight'
    task.content = 'PAR&BJS&20180921'
    task.source = 'expediaFlight'
    task.ticket_info = {"env_name":"test"}
    # task.req_qid = 111111


    def entry_test(task):
        spider = factory.get_spider_by_old_task(task)
        if spider is None:
            spider = factory.get_spider_by_old_source(task.source)
            if spider is None:
                return None
            spider.task = task
        return spider


    spider = entry_test(task)
    print spider.crawl(cache_config={'enable': False})
    print spider.result


# spider = factory.get_spider('booking', 'hotelList', required_targets=None)
# requireds = ['qyer_detail']
# # task = Task()
# # task.content = 'http://place.qyer.com/paris/sight/'
# spider = factory.get_spider_by_targets('qyer', requireds)
# spider.task = Task()
# factory.get_spider_by_old_source('')
# spider.crawl()
# test = ['cheapticketsFlight', 'expediaFlight', 'orbitzFlight', 'travelocityFlight']
# for s in test:
#     spider = factory.get_spider_by_old_source(s)
#     print spider
# task.ticket_info = {}
# task.content = 'PEK&ORD&20170419'
#
# new_spider.task = task
# new_spider.crawl()

# from mioji.common.task_info import Task
#
# new_task = Task()
# new_task.ticket_info = {}
# new_task.source = 'pricelineFlight'
# new_task.content = 'XMN&NGO&20170602'
#
# new_spider = factory.get_spider_by_old_task(new_task)
# print new_spider.crawl()
# print new_spider.result
