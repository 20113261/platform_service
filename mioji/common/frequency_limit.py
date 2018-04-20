#!/usr/bin/python
# -*- coding: UTF-8 -*-

from redlock import RedLock
import time
import uuid
import redis


# 之前的router心跳redis
#   心跳：db=1
#   请求频率控制：db=2
redis_config = {"host": "10.10.173.116", "port": 6379, "password": "MiojiRedisOrzSpiderVerify", "db": 2}

# 频率限制配置: time(s) 时间内 count 次请求限制。
#   mode：hard-严格模式，如20s 2个那么每两个请求间隔 10s；
#   soft-最近20s内不没达到2个请求就可以解析进行
limit_config = {
    "raileuropeApiRail": {"count": 1, "time": 2, "mode": "hard"},
}



class QuencyLimit:
    """
    redis_config redis配置
        LIKE: {"host": "localhost"}

    频率限制配置: time(s) 时间内 count 次请求限制。
        mode：hard-严格模式，如20s 2个那么每两个请求间隔 10s；
        soft-最近20s内不没达到2个请求就可以解析进行

        LIKE:
        {"baidu": {"count": 2, "time": 20, "mode": "soft"},
        "google": {"count": 2, "time": 20, "mode": "hard"}}
    """
    def __init__(self, redis_config, quency_config):
        self.quency_config = quency_config
        self.redlock = RedLock([redis_config])
        self.rds = redis.Redis(**redis_config)

    def block_wait(self, key, timeout=0):
        """
        :param key:
        :param timeout: TODO
        :return: True 正常控制；False 其他
        """

        # TODO 完善异常处理

        if key not in self.quency_config:
            return False

        while True:
            with red_lock(self.redlock, key):
                c = self.quency_config[key]
                if c['mode'] == 'hard':
                    hard_key = '{0}-hard'.format(key)
                    last = self.rds.get(hard_key)
                    rt = self.rds.time()
                    nt = rt[0] * 1000 + rt[1] / 1000
                    if last:
                        if nt - long(last) >= c['time'] * 1000 / c['count']:
                            self.rds.set(hard_key, nt)
                            return True
                    else:
                        self.rds.set(hard_key, nt)
                        return True

                else:
                    keys = self.rds.keys('{0}-soft:*'.format(key))
                    if len(keys) < c['count']:
                        self.rds.setex('{0}-soft:{1}'.format(key, str(uuid.uuid1())), '', self.quency_config[key]['time'])
                        return True
            time.sleep(0.5)


class SlaveLock:

    def __init__(self, redlock, key):
        self.key = key
        self.redlock = redlock
        self.lock = None

    def __enter__(self):
        while True:
            lock = self.redlock.lock(self.key, 1000)
            if not lock:
                time.sleep(0.12)
            else:
                self.lock = lock
                return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.redlock.unlock(self.lock)


def red_lock(redlock, key):
    return SlaveLock(redlock, key)


def init_default_limiter():
    # frequency_limit.init(limit_config, redis_config)
    req_limit = QuencyLimit(redis_config, limit_config)
    return req_limit


default_limiter = init_default_limiter()
