#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/6 下午8:28
# @Author  : Hou Rong
# @Site    : 
# @File    : CustomAutoScale.py
# @Software: PyCharm
import psutil
from celery.worker.autoscale import Autoscaler


class CustomAutoScale(Autoscaler):
    def _maybe_scale(self, req=None):
        memory_obj = psutil.virtual_memory()
        memory_percent = memory_obj.percent
        procs = self.processes
        if memory_percent < 50.0:
            cur = min(self.qty, self.max_concurrency)
            if cur > procs:
                self.scale_up(cur - procs)
                return True
            cur = max(self.qty, self.min_concurrency)
            if cur < procs:
                self.scale_down(procs - cur)
                return True
        else:
            self.scale_down(1)
            return True
