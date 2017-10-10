#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/6 下午8:28
# @Author  : Hou Rong
# @Site    : 
# @File    : CustomAutoScale.py
# @Software: PyCharm
import psutil
import os
from celery.worker.autoscale import Autoscaler
from proj.my_lib.logger import get_logger
from time import sleep
from celery.five import monotonic

logger = get_logger('auto scale logger')

INIT_POOL_PERCENT = 0.75


class CustomAutoScale(Autoscaler):
    def body(self):
        is_first = getattr(self, 'is_first', False)
        if is_first:
            # 首次执行时，调整为适中 process
            setattr(self, 'is_first', True)
            init_pool_size = self.min_concurrency + int(
                INIT_POOL_PERCENT * (self.max_concurrency - self.min_concurrency))
            with self.mutex:
                self._grow(init_pool_size - self.processes)
            self.pool.grow(init_pool_size - self.processes)
            self.keepalive = 60.0

        with self.mutex:
            self.maybe_scale()
        memory_obj = psutil.virtual_memory()
        memory_percent = memory_obj.percent
        if memory_percent < 85.0:
            sleep(3.0)
        elif memory_percent < 90.0:
            sleep(10.0)
        else:
            sleep(30.0)

    def _maybe_scale(self, req=None):
        worker_name = self.worker.hostname
        memory_obj = psutil.virtual_memory()
        memory_percent = memory_obj.percent
        load_average = os.getloadavg()[0]
        load_percent = load_average / 4.0
        procs = self.processes

        calc_percent = memory_percent * load_percent

        if calc_percent < 85.0:
            cur = min(self.qty, self.max_concurrency)
            if cur > procs:
                up_process = (cur - procs)
                self.scale_up(up_process)
                logger.debug("[worker_name: {}][memory_percent: {}][load_average: {}][current: {}][scale up: {}]".
                             format(worker_name, memory_percent, load_average, self.processes, up_process))
                return True
                # cur = max(self.qty, self.min_concurrency)
                # if cur < procs:
                #     self.scale_down(procs - cur)
                #     logger.debug("[worker_name: {}][memory_percent: {}][current: {}][scale down: {}]".
                #                  format(worker_name, memory_percent, self.processes, procs - cur))
                #     return True
        # elif memory_percent < 85.0:
        #     cur = max(self.qty, self.min_concurrency)
        #     if cur < procs:
        #         self.scale_down(procs - cur)
        #         logger.debug("[worker_name: {}][memory_percent: {}][current: {}][scale down: {}]".
        #                      format(worker_name, memory_percent, self.processes, procs - cur))
        #         return True
        #     else:
        #         logger.debug("[worker_name: {}][memory_percent: {}][current: {}][scale: {}]".
        #                      format(worker_name, memory_percent, self.processes, 0))
        #         return True
        # elif memory_percent < 90.0:
        #     self.scale_down(1)
        #     logger.debug("[worker_name: {}][memory_percent: {}][current: {}][scale down: {}]".
        #                  format(worker_name, memory_percent, self.processes, 1))
        #     return True
        elif calc_percent < 90.0:
            logger.debug(
                "[worker_name: {}][memory_percent: {}][load_average: {}][current: {}][scale: {}]".format(worker_name,
                                                                                                         memory_percent,
                                                                                                         load_average,
                                                                                                         self.processes,
                                                                                                         0))
            return False
        else:
            if self.processes > self.min_concurrency:
                down_process = 1
                self.scale_down(down_process)
                if self._last_scale_up and (
                                monotonic() - self._last_scale_up > self.keepalive):
                    logger.debug(
                        "[worker_name: {}][memory_percent: {}][load_average: {}][current: {}][last_scale_up: {}][scale down: {}]".
                            format(worker_name, memory_percent, load_average, self.processes, self._last_scale_up,
                                   down_process))
                else:
                    logger.debug(
                        "[worker_name: {}][memory_percent: {}][load_average: {}][current: {}][last_scale_up: {}][scale down: {}]".
                            format(worker_name, memory_percent, load_average, self.processes, self._last_scale_up,
                                   0))
                return True
