#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Created on 2016年12月19日

@author: dujun
"""
import traceback
import functools
import types
import os
import requests
import zlib
from lxml import html as HTML
import json
import time
import abc
import gevent.event
import datetime
import urllib
import uuid
import store_utils
import pika
# import pickle

from mioji.common.func_log import func_time_logger
from pool import pool
import pages_store
from browser import MechanizeCrawler
import parser_except
from logger import logger
from collections import Iterable
from pool_event_lock import block_async
from collections import defaultdict
try:
    from mioji.common.ufile_handler import multi_part_upload_stream
except:
    pass
# from mioji.common.conf_manage import ConfigHelper
from mioji.common.utils import get_md5, get_local_ip, current_log_tag
from greenlet import getcurrent

logger.debug('spider %s', __name__)

# 由用户装配
insert_db = None
get_proxy = None
# 新的
slave_get_proxy = None
need_write_file = False
is_service_platform = False

requests.packages.urllib3.disable_warnings()
update_proxy_pool = gevent.pool.Pool(20)
FORMAT_UPDATE_PROXY_URL = 'http://10.10.239.46:8087/update_proxy?source={0}&proxy={1}&error={2}&speed={3}&length={4}'

# 不要代理
PROXY_NONE = 0
# 沿用上次的设置
PROXY_FLLOW = 1
# 需要设置新代理
PROXY_REQ = 2
# 第一次
PROXY_REQ_FIRST = 3
# 永远不用代理，一般api
PROXY_NEVER = 4

MAX_FLIP = 15
NEED_FLIP_LIMIT = True

# config_helper = ConfigHelper()
debug = True

schedule_cache = {'lifetime_sec': 10 * 24 * 60 * 60, 'enable': True}
verify_cache = {'lifetime_sec': 10, 'enable': False}
none_cache = {'lifetime_sec': 0, 'enable': False}
insert_db_dict = {}

if debug:
    verify_cache = schedule_cache

TARGETS_LIST_CONFIG = {
    'hotelList_hotel': {'cache': schedule_cache},
    'hotelList_room': {'cache': schedule_cache},
    'hotelDetail_hotelinfo': {'cache': schedule_cache},
    'hotelDetail_image': {'cache': schedule_cache},
    'hotelDetail_room': {'cache': verify_cache},
    'trainList': {'cache': schedule_cache},
    'flightList_flight': {'cache': verify_cache},
    'flightDetail_flight': {'cache': verify_cache},
}

CRAWL_TYPE_LIST = ['hotelList', 'hotelDetail', 'flightList', 'flightDetail']
TARGETS_LIST = TARGETS_LIST_CONFIG.keys()


class Spider(object):
    """
    """
    __metaclass__ = abc.ABCMeta
    # 源类型
    source_type = ''
    # 抓取目标， 例如 : {'hotel':{}, 'room':{'version':'InsertNewFlight'}}
    targets = {}
    # 与老爬虫关联， 例如 : {'pricelineFlight': {'required': ['Flight']}}
    old_spider_tag = {}
    # 不启用，默认启用
    unable = False

    def __init__(self, task=None):
        # 断言 source type 以及 targets
        assert self.source_type != '', '缺失正确的抓取类型'
        assert self.targets != {}, '缺失正确的抓取 parser'
        assert len(self.targets) > 0, parser_except.ParserException(1, '必须指明解析目标')
        self.task = task
        self.task_id = str(uuid.uuid1())
        self.has_read_file = False
        self.spider_taskinfo = {}
        # 存储用户临时数据
        self.user_datas = defaultdict(list)
        # 解析目标。默认爬虫支持的所有解析目标
        self.targets_required = self.targets
        self._crawl_targets_required = self.targets_required
        self.debug = True
        self.debug_info = {'pages': []}

        self.browser = None
        self._result = defaultdict(list)
        self.code = None
        # 记录当前抓取步骤
        self.chain_count = 0

        self.is_service_platform = is_service_platform
        # 是否时验证机器
        self.is_verify = False
        self.verify_data = {'data': []}

        # 暂时没用
        self.__datas = {}
        
        #记录代理信息
        self.proxy = None

        #记录代理的所有回调
        self.update_info_list = []

        self.__targets_parser_func_dict = {}
        self.__cache_config = schedule_cache

        for t in self.targets.keys():
            self.__compute_cache(self.__cache_config, TARGETS_LIST_CONFIG.get(t, {}).get('cache', verify_cache))
            func_name = 'parse_' + t
            parse_func = getattr(self, func_name)
            self.__targets_parser_func_dict[t] = parse_func

    def __compute_cache(self, cache_config, other_cache_config):
        cache_config['enable'] &= other_cache_config['enable']
        cache_config['lifetime_sec'] = min(cache_config['lifetime_sec'], other_cache_config['lifetime_sec'])

    @property
    def crawl_targets_required(self):
        return self._crawl_targets_required

    @abc.abstractmethod
    def targets_request(self):
        """
        目标请求链：酒店列表、酒店详情、酒店评论等
        """

    def prepare_request(self, request_template):
        """
        在抓取过程中由用户指定 req，用户在函数中直接修改
        :param request_template: 本次请求的 request_template
        """
        pass

    def user_retry_err_or_resp(self, err_or_resp, retry_count, request_template, is_exc):
        """
        在 user_retry 时过程中返回错误或 response
        :param err_or_resp: 返回的错误或 response
        :param retry_count: 重试的次数
        :param request_template: 本次数据的请求的 request_template
        :param is_exc: 异常为 True，response 为 False
        :return: 如果结果正确返回 True，不返回和返回 False 都会重试
        """
        pass

    def response_callback(self, req, resp):
        """
        resp.url 判断是否是抓取页面或其他
        """
        pass

    def response_error(self,req, resp, error):
        """
        请求异常
        :param resp requests response
        :param error 异常
        """
        pass

    def get_data(self, data_key, remove_item=True):
        item = self.__datas.get(data_key, None)
        if remove_item and item is not None:
            del self.__datas[data_key]
        return item

    def __create_browser(self, create_new=False):
        if not self.browser or create_new:
            self.browser = MechanizeCrawler()
        return self.browser

    def deep_crawl(self, crawl_chain, block=True, cache_config=schedule_cache):
        if block:
            browser = self.__create_browser()
            chains = crawl_chain()
            code = self.__crawl_by_chain(browser, chains, cache_config)
            return code
        else:
            raise parser_except.ParserException(-1, '暂不支持')

    def first_url(self):
        chains = self.targets_request()
        t_req = chains[0].request()
        if isinstance(t_req, types.DictType):
            return t_req['req']

    @property
    @func_time_logger
    def result(self):
        try:
            for k, v in self._result.items():
                logger.debug(current_log_tag() + '[抓取结果][key: {0}][value_len: {1}]'.format(k, len(v)))
        except Exception:
            pass
        return self._result

    @staticmethod
    @func_time_logger
    def decompress_result(result):
        new_result = defaultdict(list)
        for k, v in result.items():
            for item in v:
                new_result[k].append(json.loads(zlib.decompress(item)))
        return new_result

    @func_time_logger
    def crawl(self, required=None, cache_config=None):
        """
        :return: (result,code)
            result like:{'hotelList_room':[(),()]}
            code: 0 全部正确；36 有翻页错误
        """
        start = time.time()
        local_ip = get_local_ip()

        if hasattr(self.task, 'new_task_id'):
            cur_id = self.task.new_task_id
        else:
            cur_id = str(uuid.uuid1())
        self.spider_taskinfo = {'task_id': cur_id}
        getcurrent().spider_taskinfo = self.spider_taskinfo

        # 当执行 crawl 时判断是否为验证任务
        start_crawl_dur = -1
        if hasattr(self.task, 'req_qid'):
            self.is_verify = True
            if hasattr(self.task, 'create_time'):
                start_crawl_dur = time.time() - self.task.create_time
                logger.debug('{0} start crawl dur: {1}'.format(current_log_tag(), start_crawl_dur))
            logger.debug(
                current_log_tag() + '[RequestServer MJOPObserver,type=sp001_{5},uid=,csuid=,qid={0},ts={1},ip={2}, '
                                    'refer_id=, cur_id={4},req={3}]'.format(
                    self.task.req_qid, time.time() * 1000, local_ip, urllib.quote(json.dumps(self.task.__dict__)),
                    cur_id, self.task.source
                )
            )

        # 打印任务信息日志
        for k, v in self.task.__dict__.items():
            self.spider_taskinfo[k] = v
            try:
                logger.info(current_log_tag() + '[任务信息][%s][%s]' % (k, json.dumps(v)))
            except Exception:
                continue
        # 缓存配置
        if not cache_config:
            # 未指定
            cache_config = self.__cache_config
            if required is not None:
                cache_config = schedule_cache
                for target in required:
                    self.__compute_cache(cache_config,
                                         TARGETS_LIST_CONFIG.get(target, {}).get('cache', none_cache))

        if required is not None:
            self._crawl_targets_required = required
        else:
            self._crawl_targets_required = self.targets_required

        # browser
        browser = self.__create_browser()
        chains = self.targets_request()
        try:
            self.code = self.__crawl_by_chain(browser, chains, cache_config)
        except parser_except.ParserException as e:
            logger.exception(e)
            self.code = e.code

        # 通过返回的全部 result 判断错误码
        self.check_all_result()

        if self.is_verify:
            self.verify_data['source'] = self.task.source
            cost_time = time.time() - start
            self.verify_data['cost'] = cost_time
            self.verify_data['error_code'] = self.code
            logger.debug(
                current_log_tag() + '[ResponseServer MJOPObserver,type=sp001_{6},uid=,csuid=,qid={0},ts={1},ip={2}, '
                                    'refer_id=, cur_id={5},resp={3},cost={4}]'.format(
                    self.task.req_qid, time.time() * 1000, local_ip, urllib.quote(json.dumps(self.verify_data)),
                    cost_time, cur_id, self.task.source, 
                )
            )

            if hasattr(self.task, 'create_time'):
                total = time.time() - self.task.create_time
                logger.debug(current_log_tag() +
                             ',crawl end,crawl_dur={0},total={1},crawl_cost={2},code={3},crawled={4}'
                             .format(start_crawl_dur, total, cost_time, self.code, self._crawled_count()))

        
        return self.code

    def _crawled_count(self):
        if not self.result:
            return 0
        crawled = {}
        for k, v in self.result.items():
            crawled[k] = len(v)
        return crawled

    def check_all_result(self):
        """
        在其中判断全部 result 的状态码，爬虫可以重写
        self.result 为返回的所有结果
        self.code 为将要返回的状态码
        :return: 无需返回，直接修改 self.code 即可
        """
        # 只针对误判的 0 进行操作
        if self.code == 0:
            # 默认通过数据状况判断 29
            if not self.result:
                self.code = 29

            for k, v in self.result.items():
                if not v:
                    self.code = 29

        if self.code == 29:
            if self.result:
                for k, v in self.result.items():
                    if v:
                        self.code = 36

    @func_time_logger
    def __crawl_by_chain(self, browser, chains, cache_config):
        code = 0
        try:
            # 请求链
            for reqParse in chains:
                # 抓取步骤记录
                self.chain_count += 1

                # 请求开始
                reqParse.spider = self
                t_req = reqParse.request()
                if isinstance(t_req, types.DictType):
                    # 单一请求不支持使用 multi
                    reqParse.multi = False

                    # 单一请求
                    try:
                        browser = self.__create_browser(reqParse.new_session)
                        new_result = self.__single_crawl(reqParse, browser, t_req, cache_config, 0)
                        self.__spider_append_result(new_result)
                    except parser_except.ParserException as e:
                        if e.code == 95:
                            code = 95
                            break
                        else:
                            raise e

                elif isinstance(t_req, types.ListType):
                    logger.debug(current_log_tag() + "%s, len %s,", t_req, len(t_req))

                    # 请求队列，一般是pages
                    if not t_req:
                        # 没有分页
                        continue

                    browser = self.__create_browser(reqParse.new_session)
                    if reqParse.async:
                        # 并行抓取页
                        list_result = self.__async_crawl_list(reqParse, browser, t_req,
                                                              cache_config)
                    else:
                        # 串行
                        list_result = self.__crawl_list(reqParse, browser, t_req, cache_config)

                    # 对 multi 的情况进行特殊处理
                    if reqParse.multi:
                        # 生成 template 和 data 的链表
                        try:
                            template_list, convert_data_list = list(zip(*list_result[0].values()[0]))
                        except Exception:
                            raise parser_except.ParserException(parser_except.PROXY_INVALID, '代理异常')

                        try:
                            list_result = reqParse.parse(template_list, self.__targets_parser_func_dict,
                                                         convert_data_list, 0,
                                                         self._crawl_targets_required, True)
                            self.__spider_append_result(list_result)
                        except parser_except.ParserException as e:
                            raise e
                        except Exception:
                            raise parser_except.ParserException(parser_except.PARSE_ERROR,
                                                                '[traceback:{0}]'.format(traceback.format_exc()))

                    else:
                        new_result, code = self.check_list_result(list_result)
                        self.__spider_append_result(new_result)

                elif isinstance(t_req, types.GeneratorType):
                    # 生成一个请求抓取一个，request_template 使用 yield 实现。用于需要抓取页面生成下一页抓取请求
                    try:
                        browser = self.__create_browser(reqParse.new_session)
                        list_result = self.__crawl_list(reqParse, browser, t_req, cache_config)
                    except Exception:
                        raise parser_except.ParserException(parser_except.PROXY_INVALID, '代理异常')

                    # 对 multi 的情况进行特殊处理
                    if reqParse.multi:
                        # 生成 template 和 data 的链表
                        template_list, convert_data_list = list(zip(*list_result[0].values()[0]))
                        try:
                            list_result = reqParse.parse(template_list, self.__targets_parser_func_dict,
                                                         convert_data_list, 0,
                                                         self._crawl_targets_required, True)
                            self.__spider_append_result(list_result)
                        except parser_except.ParserException as e:
                            raise e
                        except Exception:
                            raise parser_except.ParserException(parser_except.PARSE_ERROR,
                                                                '[traceback:{0}]'.format(traceback.format_exc()))

                    else:
                        new_result, code = self.check_list_result(list_result)
                        self.__spider_append_result(new_result)
                else:
                    raise parser_except.ParserException(1, 'not support request template {0}'.format(t_req))
        except parser_except.ParserException as e:
            logger.error(e)
            raise e
        except Exception:
            logger.exception(
                current_log_tag() + '[新框架 持续请求 未知问题][ {0} ]'.format(traceback.format_exc().replace('\n', '\t')))
            raise parser_except.ParserException(parser_except.UNKNOWN_ERROR, 'e:{0}'.format(traceback.format_exc()))

        return code

    @staticmethod
    @func_time_logger
    def get_db_func(version):
        if not insert_db:
            raise parser_except.ParserException(parser_except.STORAGE_ERROR, 'please define insert_db')

        if version not in insert_db_dict:
            insert_db_dict[version] = getattr(insert_db, version)

        return insert_db_dict[version]

    @func_time_logger
    def store(self):
        if debug:
            logger.debug(current_log_tag() + 'can’t store data')
            return None

        un_known_data = []
        db_exception = []
        insert_db_ok = True
        insert_rabbitmq_ok = True
        result = self.result
        for k, v in result.items():
            version = self.targets.get(k, {}).get('version')
            if version:
                try:
                    res = self.get_db_func(version=version)(v)
                    if isinstance(res, tuple):
                        if len(res) == 2:
                            insert_rabbitmq_ok, insert_db_ok = res
                except Exception, e:
                    db_exception.append(e)
                    pass
            else:
                un_known_data.append(k)
        if un_known_data:
            raise parser_except.ParserException(parser_except.STORAGE_ERROR,
                                                'un_known_data:{0};'.format(un_known_data))
        if not insert_rabbitmq_ok and not insert_db_ok:
            raise parser_except.ParserException(parser_except.RABBITMQ_MYSQL_ERROR, '入库 mysql RabbitMQ 均发生异常')
        if not insert_rabbitmq_ok and insert_db_ok:
            raise parser_except.ParserException(parser_except.RABBITMQ_ERROR, 'RabbitMQ 入库异常')
        if not insert_db_ok and insert_rabbitmq_ok:
            raise parser_except.ParserException(parser_except.MYSQL_ERROR, 'MySQL 入库异常')
        if db_exception:
            raise parser_except.ParserException(parser_except.STORAGE_UNKNOWN_ERROR,
                                                'db_exception:{0}'.format(db_exception))

    def __async_crawl_list(self, reqParse, browser, req_list, cache_config):
        """
        并行抓取分页
        """
        a_result = defaultdict(list)
        all_except = True
        all_ok = True
        one_exception = None

        params = []
        total_count = 0
        for req in req_list:
            # 并行增加翻页限制
            if NEED_FLIP_LIMIT:
                if total_count >= MAX_FLIP:
                    break
            total_count += 1
            params.append((reqParse, browser, req, cache_config, total_count))

        result = block_async(pool, self.__single_crawl, params)

        success_count = 0
        error_req = []
        for a_res in result:
            err_or_data, is_data = a_res
            if is_data:
                success_count += 1
                all_except = False
                self.__append_result(a_result, err_or_data)
            else:
                all_ok = False
                args, kwargs, one_exception = err_or_data
                error_req.append((args[2], one_exception.message))
        logger.debug(current_log_tag() + '[翻页抓取][并行抓取][ 成功 {0} / {1} ]'.format(success_count, len(req_list)))
        if error_req:
            logger.debug(current_log_tag() + '[翻页抓取][并行抓取][ 失败页请求 {0} ]'.format(str(error_req)))
        return a_result, all_except, all_ok, one_exception

    def __crawl_list(self, reqParse, browser, req_list, cache_config):
        """
        串行抓取分页
        """
        result = defaultdict(list)
        all_except = True
        all_ok = True
        one_exception = None

        total_count = 0
        success_count = 0
        error_req = []
        for req in req_list:
            # 串行增加翻页限制
            if NEED_FLIP_LIMIT:
                if total_count >= MAX_FLIP:
                    break
            total_count += 1
            try:
                success_count += 1
                res = self.__single_crawl(reqParse, browser, req, cache_config, page_count=total_count)
                self.__append_result(result, res)
                all_except = False
            except Exception, e:
                all_ok = False
                one_exception = e
                error_req.append((req, one_exception.message))
                logger.exception(
                    current_log_tag() + '[新框架][页面解析异常][ {0} ]'.format(traceback.format_exc().replace('\n', '\t')))

                #  抛出生成器部分的异常
                if isinstance(req, types.GeneratorType):
                    raise e

        logger.debug(current_log_tag() + '[翻页抓取][串行抓取][ 成功 {0} / {1} ]'.format(success_count, total_count))
        if error_req:
            logger.debug(current_log_tag() + '[翻页抓取][串行抓取][ 失败页请求 {0} ]'.format(str(error_req)))
        return result, all_except, all_ok, one_exception

    @staticmethod
    def __append_result(result, new_result):
        """
        向 result 中添加数据
        :param result: 被添加量
        :param new_result: 添加量
        :return: None
        """
        for k, v in new_result.items():
            if not v:
                continue
            logger.debug(current_log_tag() + "%s, length=%s, all=%s", k, len(v), len(result.get(k, [])))
            result[k] += v

    def __spider_append_result(self, new_result):
        """
        向 self.result 中添加解析结果
        :param new_result: 必须为解析结果
        :return: None
        """
        for k, v in new_result.items():
            if not v:
                continue
            data_bind = self.targets[k].get('bind', None)
            if data_bind:
                logger.debug("current_log_tag() + [ 抓取绑定 {0} ][ 数据绑定 {1} ]".format(k, data_bind))
                self._result[data_bind] += v
                logger.debug(current_log_tag() + "%s, length=%s, all=%s", k, len(v), len(self._result.get(k, [])))
            else:
                self._result[k] += v
                logger.debug(current_log_tag() + "%s, length=%s, all=%s", k, len(v), len(self._result.get(k, [])))

    def cache_check(self, req, data):
        return True

    @func_time_logger
    def __single_crawl(self, reqParse, browser, request_template, cache_config, page_count):
        # for k, v in request_template['req'].items():
        #     logger.debug('[请求开始][req][ {0} : {1} ]'.format(k, v))
        headers = request_template['req'].get('headers', None)
        if headers:
            browser.add_header(headers)

        cache_str, md5 = pages_store.get(cache_config, request_template['req'])

        convert_data = None
        is_first = True

        # load from cache
        if cache_str:
            logger.debug(current_log_tag() + '[使用缓存][ {0} ]'.format(request_template['req']['url']))
            try:
                convert_data = reqParse.convert(request_template, cache_str)
                if not self.cache_check(request_template['req'], convert_data):
                    convert_data = None
                    logger.debug(current_log_tag() + '[缓存过期][ {0} ]'.format(request_template['req']['url']))
                if self.debug:
                    self.debug_info['pages'].append(md5)
            except Exception, e:
                logger.warning(current_log_tag() + 'cache error')
                convert_data = None

        # 设置 res 的 默认值
        res = defaultdict(list)

        # 初始化请求参数
        reqParse.req_count = 0
        reqParse.is_forbidden = False
        reqParse.req_exception = None
        reqParse.proxy = None
        reqParse.content_length = 0

        # 针对解析中抛出的 22， 23 错误，重新从网络上抓取
        while reqParse.req_count < reqParse.retry_count:
            # 增加一次重试次数
            reqParse.req_count += 1
            # 首次使用缓存，之后出现抓取异常则清除 convert_data 重新抓取
            if is_first:
                is_first = False
            else:
                convert_data = None

            # 抓取和数据转换部分
            if not convert_data:
                logger.debug(current_log_tag() + '[开始抓取][ {0} ]'.format(request_template['req']['url']))
                # 外部传入请求次数，用于在 parse 过程中抛出的代理异常进行重新抓取
                try:
                    resp = reqParse.crawl_data(request_template, browser, self.task.source)
                except parser_except.ParserException as e:
                    if reqParse.user_exc:
                        # 抛出用户在函数中抛出的错误
                        raise e
                    if e.code in (parser_except.PROXY_FORBIDDEN, parser_except.PROXY_INVALID, parser_except.REQ_ERROR):
                        reqParse.is_forbidden = True

                        if reqParse.req_count >= reqParse.retry_count:
                            raise e
                        else:
                            logger.debug(current_log_tag() + traceback.format_exc())
                            logger.debug(current_log_tag() + '[准备重试][错误由框架抛出][错误码：{0}]'.format(e.code))
                            convert_data = None
                            continue
                    else:
                        raise e
                except Exception, e:
                    if reqParse.user_exc:
                        # 抛出用户在函数中抛出的错误
                        raise e
                    if reqParse.req_count >= reqParse.retry_count:
                        raise e
                    else:
                        continue

                # 请求中增加 resp 的值
                request_template['resp'] = resp

                # 打印存储抓取结果
                self.response_callback(request_template, resp)
                res = resp.text
                try:
                    logger.debug(
                        current_log_tag() + '[抓取结果][ {2} ][ {0} ... ... {1} ]'.format(res[:100], res[-100:],
                                                                                      request_template['req'][
                                                                                          'url']).replace('\n',
                                                                                                          '').replace(
                            '\t', ''))
                    md5 = pages_store.put(cache_config, request_template['req'], res)
                    if self.debug:
                        self.debug_info['pages'].append(md5)
                except Exception:
                    pass

                # 如果验证，则保存这一部分网页
                if self.is_verify:
                    md5_key = get_md5(res)
                    verify_task_info = {
                        'func_name': reqParse.request_func.__name__,
                        'page_index': page_count,
                        'retry_count': reqParse.req_count - 1,
                        'md5_key': md5_key
                    }

                    if multi_part_upload_stream:
                        if multi_part_upload_stream(md5_key, res):
                            logger.debug(current_log_tag() + '[验证页面上传成功] md5:{0}'.format(md5_key))
                        else:
                            logger.debug(current_log_tag() + '[验证页面上传失败]')

                    self.verify_data['data'].append(verify_task_info)

                # 数据转换
                try:
                    convert_data = reqParse.convert(request_template, res)
                except Exception:
                    if reqParse.req_count < reqParse.retry_count:
                        continue
                    else:
                        logger.debug(current_log_tag() + traceback.format_exc())
                        raise parser_except.ParserException(parser_except.DATA_FORMAT_ERROR,
                                                            '[traceback: {0}]'.format(traceback.format_exc()))

            # 数据解析部分
            try:
                res = reqParse.parse(request_template, self.__targets_parser_func_dict, convert_data, page_count,
                                     self._crawl_targets_required)
                break
            except parser_except.ParserException as e:
                if e.code in (parser_except.PROXY_FORBIDDEN, parser_except.PROXY_INVALID):
                    reqParse.is_forbidden = True

                    if reqParse.req_count >= reqParse.retry_count:
                        raise e
                    else:
                        logger.debug(current_log_tag() + '[准备重试][错误由爬虫抛出][错误码：{0}]'.format(e.code))
                        convert_data = None
                        continue
                else:
                    raise e
            except Exception:
                raise parser_except.ParserException(parser_except.PARSE_ERROR,
                                                    '[traceback:{0}]'.format(traceback.format_exc()))

        return res

    def check_list_result(self, list_result):
        """
        检查每一个请求项返回的页面内容
        :param list_result: result, all_except, all_ok, one_exception 传入四项参数，返回的结果列表，是否全部为异常，是否全部正常
        :return:
        result like:{'hotelList_room':[(),()]}
        code: 0 全部正确；36 有翻页错误
        """
        # """
        # :return: (result,code)
        #     result like:{'hotelList_room':[(),()]}
        #     code: 0 全部正确；36 有翻页错误
        # """
        '''
        # 这个判断需要很复杂，所以目前来说先禁用，如果有结果返回0,没有结果返回29
        # 还是希望在爬虫模块来判定问题。目前来说这个判定太严格，导致返回的错误码其实是有问题的
        result, all_except, all_ok, one_exception = list_result
        if all_except:
            raise parser_except.ParserException(36, one_exception.msg)

        return result, 0 if all_ok else parser_except.FLIP_WARRING
        '''
        '''
        # 修改判断条件，在最外层判断，0 和 29 ，此处只给出 全部异常的 37
        '''
        '''
        此处对37逻辑的判断影响了expedia ctrip 等爬虫的正确错误码返回暂改成用爬虫的
        '''
        if not self.is_verify:
            result, all_except, all_ok, one_exception = list_result
            if all_except:
                # return result, 37
                return result, one_exception.code
            else:
                return result, 0
        else:
            result, all_except, all_ok, one_exception = list_result
            if all_ok and not all_except:
                if result:
                    return result, 0
                else:
                    return result, 0
            elif result and not all_except:
                return result, 36
            elif not all_except:
                return result, 0
            else:
                return result, 37


def request(retry_count=3, proxy_type=PROXY_REQ, async=False, binding=None, user_retry_count=0,
            user_retry=False, multi=False, content_length=0, new_session=False, ip_type="test", ip_num=1):
    """
    :param retry_count: 请求重试次数
    :param proxy_type: 代理类型
    :param async: 多个req是否需要同步
    :param binding: 绑定的解析函数，支持 None, str, bytes, callable, 以及可迭代的前几种类型
    :param user_retry: 用户重试，将重试部分教给用户操作。标记为 True 后，会增加 user_retry_err_or_resp handler 交由用户处理重试部分
    :param multi: 是否为同时进行多个解析。标记为 True 后，将会在爬取全部页面后返回所有页面值。在 parse 函数中返回的 req 和 data 分别为 list 。
    :param content_length: 是否需要判断 content_length 合法，None 不需要判断，0 或其他正整数，content_length 需要大于设置值
    :param new_session: 新的browser session
    :return: 返回 ReqParse 类型
    :ip_type: 决定使用国内代理(internal)还是国外(foreign)的
    """

    def call(func):
        req = ReqParse(func, retry_count, proxy_type, async, binding, user_retry_count,
                       user_retry, multi, content_length, new_session, ip_type, ip_num)
        return req

    return call


def mioji_data(version=0):
    """
    数据版本
    """

    def call(func):
        @functools.wraps(func)
        def _call(*args, **kw):
            target_list = func(*args, **kw)
            return target_list

        return _call

    return call


# data request and parse
class ReqParse(object):
    def __init__(self, func, retry_count=3, proxy_type=PROXY_REQ, async=False, binding=None, user_retry_count=0,
                 user_retry=False, multi=False, content_length=0, new_session=False, ip_type="test", ip_num=1):
        self.__request_func = func
        if user_retry_count:
            self.retry_count = user_retry_count
        else:
            # 强制4次重试
            self.retry_count = 4

        self.proxy_type = proxy_type
        self.async = async
        self.binding = binding
        self.req_count = 0

        self.request_template = None
        self.__result = None
        self.spider = None
        self.user_retry = user_retry
        self.user_exc = False
        self.need_content_length = content_length

        # 是否返回此种类型所有页面
        self.multi = multi

        # 初始化抓取标志
        self.is_forbidden = False
        self.req_exception = None
        self.proxy = None
        self.content_length = 0

        #代理ip所需类型，国内or国外
        self.ip_type = ip_type

        #代理ip请求数量
        self.ip_num = ip_num

        #此处存放代理回调信息
        self.proxy_update_info_list = []

        # session browser
        self.new_session = new_session

    @property
    def request_func(self):
        return self.__request_func

    def request(self):
        return self.__request_func()

    def __crawl_data_str(self, request_template, browser):
        resp = None
        try:
            # 使用方法修改，用户直接修改 request_template 中的值
            self.spider.prepare_request(request_template)

            # 获得 request_template 中的 req
            req = request_template['req']

            # 请求
            # resp = browser.req(req['url'], method=req.get('method', 'get'), params=req.get('params', None),
            #                    data=req.get('data', None), timeout=req.get('timeout', (60, None)),
            #                    verify=req.get('verify', False),
            #                    headers=req.get('headers', None), cookies=req.get('cookies', None), **req)

            resp = browser.req(**req)
            # 网络错误，异常抛出
            resp.raise_for_status()
            content_length = len(resp.content)
            if isinstance(self.need_content_length, int):
                logger.debug(
                    current_log_tag() + '[爬虫 content_length={1} 检测][页面长度需要大于 {0}]'.format(self.need_content_length, content_length))
                if content_length <= self.need_content_length:
                    raise parser_except.ParserException(parser_except.PROXY_INVALID, msg='data is empty')
            elif self.need_content_length is None:
                logger.debug(current_log_tag() + '[爬虫无需 content_length 检测]')
            else:
                logger.debug(
                    current_log_tag() + '[未知 content_length 检测类型][type: {0}]'.format(
                        str(type(self.need_content_length))))
            return resp, content_length

        except requests.exceptions.Timeout as e:  # timeout
            self.spider.response_error(request_template, resp, e)
            raise parser_except.ParserException(parser_except.PROXY_FORBIDDEN, msg='Request Timeout')
        except requests.exceptions.ProxyError as e:  # 代理失效
            self.spider.response_error(request_template, resp, e)
            raise parser_except.ParserException(parser_except.PROXY_INVALID, msg='Request Timeout')
        except requests.exceptions.HTTPError as err:  # 4xx 5xx 的错误码会catch到
            self.spider.response_error(request_template, resp, err)
            raise parser_except.ParserException(parser_except.PROXY_INVALID, msg=str(err))
        except requests.exceptions.ConnectionError as err:
            self.spider.response_error(request_template, resp, err)
            raise parser_except.ParserException(parser_except.PROXY_INVALID, msg=str(err))
        except requests.exceptions.RequestException as err:  # 这个是总的error
            self.spider.response_error(request_template, resp, err)
            raise parser_except.ParserException(parser_except.PROXY_INVALID, msg=str(err))
        except Exception as e:  # 这个是最终的error
            self.spider.response_error(request_template, resp, e)
            raise parser_except.ParserException(parser_except.PROXY_INVALID, msg=traceback.format_exc())

    def crawl_data(self, request_template, browser, source_name):
        """
        页面抓取函数
        :param request_template: 请求字典
        :param browser: 抓取浏览器
        :param source_name: 源名称
        :return: 返回抓取结果 response 对象
        """
        try:
            logger.debug(current_log_tag() + 'crawl %s, retry_count: %s', self.__request_func.__name__, self.req_count)
            # 代理装配
            # 不使用代理、永远不使用代理
            # if self.proxy_type == PROXY_NONE or self.proxy_type == PROXY_NEVER:
            #     browser.set_proxy(None)
            # # 请求代理 或 "被封禁 且 不是永远不使用代理" 主动设置代理
            # if self.proxy_type == PROXY_REQ or self.is_forbidden:
            #     verify_info = "master"
            #     is_recv_real_time_request = config_helper.is_recv_real_time_request
            #     if is_recv_real_time_request:
            #         verify_info = "verify"
            #     if not self.spider.is_verify and self.spider.is_service_platform:
            #         verify_info = "platform"
            #     # import pdb
            #     # pdb.set_trace()
            #     proxy_info = w_get_proxy(source=source_name, task=self.spider.task, ip_type=self.ip_type, ip_num=self.ip_num, verify_info=verify_info)
            #
            #     if proxy_info != "REALTIME" and proxy_info:
            #         self.proxy = proxy_info
            #         self.spider.proxy = self.proxy
            #         proxy = proxy_info[0]
            #     else:
            #         proxy = proxy_info
            #     browser.set_proxy(proxy)
            resp, self.content_length = self.__crawl_data_str(request_template, browser)
           
            # todo 修改 user_retry 返回的结果
            if self.user_retry:
                try:
                    user_check = self.spider.user_retry_err_or_resp(resp, self.req_count, request_template, False)
                except Exception as e:
                    self.user_exc = True
                    raise e

                # 当用户返回 True 时
                if user_check:
                    return resp
                else:
                    raise parser_except.ParserException(parser_except.PROXY_INVALID,
                                                        '代理异常')
            else:
                return resp
        except parser_except.ParserException, e:
            self.is_forbidden = e.code in (
                parser_except.PROXY_FORBIDDEN, parser_except.PROXY_FORBIDDEN, parser_except.REQ_ERROR)
            self.req_exception = e
        except Exception, e:
            self.req_exception = parser_except.ParserException(parser_except.REQ_ERROR, 'req exception:{0}'.format(e))

            # 如果有用户异常，则置位用户重试
            if self.user_exc:
                if isinstance(e, parser_except.ParserException):
                    self.req_exception = e

        finally:
            if self.req_exception:
                code = self.req_exception.code
            else:
                code = 0
            # 代理反馈
            # import pdb
            # pdb.set_trace()
            try:
                if self.proxy and self.proxy_type != PROXY_FLLOW and self.proxy != "REALTIME":            
                    proxy_update_info = (
                        {
                            "proxy_info": self.proxy,
                            "code": code,
                            "task": self.spider.task
                        }
                    )
                    logger.info("本步抓取代理回调信息：{0}".format(proxy_update_info))
                    w_update_proxy_test(self.proxy, code, self.spider.task)
            except:
                logger.debug("代理回调写入失败")
                # else:
                #     w_update_proxy_online(source_name, self.proxy[0], code, 0, self.content_length)
                

        if self.req_exception:
            raise self.req_exception

    @func_time_logger
    def convert(self, request_template, data):
        data_con = request_template.get('data', {})
        c_type = data_con.get('content_type', 'string')
        logger.debug(current_log_tag() + 'Converter got content_type: %s', c_type)
        if c_type is 'html':
            return HTML.fromstring(data)
        elif c_type is 'json':
            return json.loads(data)
        elif isinstance(c_type, types.MethodType):
            try:
                return c_type(request_template, data)
            except:
                raise parser_except.ParserException(-1, 'convert func muset error{0} ,func：{1}'.format(
                    traceback.format_exc(), c_type))
        else:
            return data

    @func_time_logger
    def parse(self, request_template, targets_bind, converted_data, page_index, required=None, multi_last=False):
        result = defaultdict(list)
        parsed = set()
        if not multi_last:
            parser_list = request_template.get('user_handler', [])
            for parser in parser_list:
                if parser not in parsed:
                    logger.debug(current_log_tag() + 'user parser %s', parser)
                    parser(request_template, converted_data)

        # 通过 parse 更新 result 信息
        def parse_result(parser):
            # 判断是否为有解析需要，且在需解析目标中
            parser_name = parser.__name__.split('_', 1)[1]
            if parser_name in required:
                logger.debug(current_log_tag() + 'parse target %s', parser_name)
                if self.multi and not multi_last:
                    # 当 multi 时只存储，不解析
                    result[parser_name].append((request_template, converted_data))
                else:
                    # 非 multi 和 multi 的最后一次进行解析
                    per_result = parser(request_template, converted_data)
                    if per_result is not None:
                        if per_result:
                            start = datetime.datetime.now()
                            if isinstance(per_result, types.ListType):
                                # 添加 guest_info
                                store_utils.add_index_info(
                                    self.spider.targets.get(parser_name, {}).get('version', None),
                                    per_result, page_index)
                                # 添加 stopby 信息
                                store_utils.add_stop_by_info(
                                    self.spider.targets.get(parser_name, {}).get('version', None),
                                    per_result, self.spider.task)
                                result[parser_name].extend(per_result)
                            elif isinstance(per_result, types.DictType):
                                result[parser_name].append(per_result)
                            logger.debug(
                                current_log_tag() + '[结果保存][不使用压缩][用时： {0} ]'.format(
                                    datetime.datetime.now() - start))

        # 解析目标，酒店、房间、等
        # for target, parser in targets_bind.items():
        if isinstance(self.binding, Iterable) and not isinstance(self.binding, (str, bytes)):
            for binding in self.binding:
                # 对 binding 种类进行兼容判断
                if binding is None:
                    continue
                elif isinstance(binding, (str, bytes)):
                    parser = targets_bind.get(binding, '')
                    if parser == '':
                        TypeError('无法从 targets 中获取 parser {0}'.format(binding))
                elif callable(binding):
                    parser = binding
                else:
                    raise TypeError('不支持绑定类型 {0} 的 {1}'.format(type(binding), repr(binding)))
                # 更新 result 信息
                parse_result(parser)

        elif isinstance(self.binding, (str, bytes)):
            parser = targets_bind.get(self.binding, '')
            if parser == '':
                TypeError('无法从 targets 中获取 parser {0}'.format(self.binding))

            # 更新 result 信息
            parse_result(parser)

        elif callable(self.binding):
            parser = self.binding
            # 更新 result 信息
            parse_result(parser)

        return result


# other
def w_get_proxy(source, task, ip_type, ip_num, verify_info):
    if debug and not slave_get_proxy:
        print 'debug，and not define get_proxy，so can’t get proxy '
        return None
    p = slave_get_proxy(source=source, task=task, ip_type=ip_type, ip_num=ip_num, verify_info=verify_info)
    if not p:
        raise parser_except.ParserException(parser_except.PROXY_NONE, 'get {0} proxy None'.format(source))
    return p


def w_block_update_proxy(source, proxy, code, speed, length):
    requests.get(FORMAT_UPDATE_PROXY_URL.format(source, proxy, code, speed, length))


def w_update_proxy_online(source, proxy, code, speed, length):
    if debug:
        return None
    update_proxy_pool.apply_async(w_block_update_proxy, (source, proxy, code, speed, length))

def w_update_proxy_test(proxy_infos, code, task):

    update_proxy_pool.apply_async(w_update_proxy_test_info, (proxy_infos,code, task))


def w_update_proxy_test_info(proxy_infos, code, task):
    logger.debug('[rabbitmq 入库开始]')
    try:
        res = None
        credentials = pika.PlainCredentials(username="writer", password="miaoji1109")
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host="10.10.160.200", port=5672, virtual_host='offline', credentials=credentials
            )
        )
        channel = connection.channel()
        channel.queue_declare(queue="spiderToProxy", durable=True)

        channel.exchange_declare(exchange='spider', durable=True)
        req_info = proxy_infos[1][2]
        proxy_info = json.loads(proxy_infos[1][0])
        proxy_time = proxy_infos[1][1]
        source = proxy_info['resp'][0]['source']
        external_ip = proxy_info['resp'][0]['ips'][0]['external_ip']
        inner_ip = proxy_info['resp'][0]['ips'][0]['inner_ip']

        qid = str(task.ticket_info.get('qid',0))

        args = {"source": source,
            "external_ip": external_ip,
            "inner_ip": inner_ip,
            "error_code": str(code),
            "cost": str(int(proxy_time)),
            "qid": qid,
            "req_info":req_info
            }
        msg = json.dumps({"callback": args}, ensure_ascii=True)
        logger.info("mq入库信息：{0}".format(msg))
        res = channel.basic_publish(exchange='spider', routing_key="spider_proxy", body=msg, properties=pika.BasicProperties(delivery_mode=2))
        connection.close()
    except Exception as e:
        logger.error("爬虫代理回调写mq出错，{0},".format(e))
    if not res:
        logger.error("爬虫代理回调写mq出错,res为空")
    logger.info("mq入库成功")

def task_wrapper(func):
    """
    apply_async 是在结果成功时调用 callback 中的函数，通过此方法将异常返回
    :param func: task 函数，例如：self.__single_crawl
    :return: 返回 函数结果 或 函数异常，以及为哪一者
    """

    @functools.wraps(func)
    def call(*args, **kwargs):
        try:
            return func(*args, **kwargs), True
        except Exception as exc:
            return exc, False

    return call