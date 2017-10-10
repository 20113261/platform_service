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

logger = get_logger('auto scale logger')


class CustomAutoScale(Autoscaler):
    def _maybe_scale(self, req=None):
        worker_name = self.worker.hostname
        memory_obj = psutil.virtual_memory()
        memory_percent = memory_obj.percent
        procs = self.processes
        if memory_percent < 85.0:
            cur = min(self.qty, self.max_concurrency)
            if cur > procs:
                up_process = (cur - procs)
                self.force_scale_up(up_process)
                logger.debug("[worker_name: {}][memory_percent: {}][current: {}][scale up: {}]".
                             format(worker_name, memory_percent, self.processes, up_process))
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
        elif memory_percent < 90.0:
            logger.debug(
                "[worker_name: {}][memory_percent: {}][current: {}][scale: {}]".format(worker_name, memory_percent,
                                                                                       self.processes, 0))
            return True
        else:
            cur = procs - self.min_concurrency
            # down_process = max(int(cur / 2), 1)
            down_process = 2
            # self.scale_down(down_process)
            self.force_scale_down(down_process)
            logger.debug("[worker_name: {}][memory_percent: {}][current: {}][scale down: {}]".
                         format(worker_name, memory_percent, self.processes, down_process))
            return True
