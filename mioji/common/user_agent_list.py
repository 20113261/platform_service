#!/usr/bin/python
# -*- coding: UTF-8 -*-
import random
from user_agents import parse
from fake_useragent import UserAgent
from logger import logger


def random_useragent():
    pro_ua = True
    us_ag = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
    while pro_ua:
        ua = UserAgent
        sa = ua().random
        user_agent = parse(sa)
        if user_agent.browser.family == 'IE' and user_agent.browser.version > 8:
            us_ag = sa
            pro_ua = False
        elif user_agent.browser.family == 'Firefox' and user_agent.browser.version > 13:
            us_ag = sa
            pro_ua = False
        elif user_agent.browser.family == 'Chrome' and user_agent.browser.version > 20:
            us_ag = sa
            pro_ua = False
        else:
            pass
    logger.info('user_agent:%s' % us_ag)
    return us_ag

if __name__ == '__main__':
    print random_useragent()
