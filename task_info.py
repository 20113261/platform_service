#coding:utf-8
# @Time    : 2018/5/22
# @Author  : xiaopeng
# @Site    : boxueshuyuan
# @File    : task_info.py
# @Software: PyCharm

class Task(object):
    # worker = ''  # 'proj.total_tasks.hotel_detail_task'
    # queue = ''  # 'hotel_detail'
    # routine_key = ''  # 'hotel_detail'
    # task_name = ''  # task_tag
    # source = ''  # source.title()
    # _type = ''  # 'Hotel'

    def __init__(self, worker, queue, routine_key, task_name, source, _type, kwargs):
        self.worker = worker
        self.queue = queue
        self.routine_key = routine_key
        self.task_name = task_name
        self.source = source
        self._type = _type
        assert self.worker != '', '缺失正确的抓取类型'
        assert self.queue != '', '缺失正确的抓取类型'
        assert self.routine_key != '', '缺失正确的抓取类型'
        assert self.task_name != '', '缺失正确的抓取类型'
        assert self.source != '', '缺失正确的抓取类型'
        assert self._type != '', '缺失正确的抓取类型'

