#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月9日

@author: dujun
'''

import datetime
import json

TASK_DATE_FORMAT = '%Y%m%d'


class Task(object):
    def __init__(self, source='demo', content=None, extra={}):
        self.source = source
        self.content = content
        self.extra = extra
        self.ticket_info = {}

    def init_ticket_info(self, source, ticket_info):
        if not ticket_info:
            return

        source = source.lower()
        if 'flight' in source:
            ticket_info.setdefault('v_seat_type', 'E')
            count = int(ticket_info.setdefault('v_count', 2))
            ticket_info.setdefault('v_age', '_'.join(['-1'] * count))
            ticket_info.setdefault('v_hold_seat', '_'.join(['1'] * count))

        elif 'hotel' in source:
            ticket_info.setdefault('room_info', [])
            ticket_info.setdefault('occ', 2)
            ticket_info.setdefault('room_count', 1)

        elif 'train' in source:
            ticket_info.setdefault('v_seat_type', '2nd')
            count = int(ticket_info.setdefault('v_count', 2))
            ticket_info.setdefault('v_age', '_'.join(['-1'] * count))
            ticket_info.setdefault('v_hold_seat', '_'.join(['1'] * count))

        elif 'bus' in source:
            ticket_info.setdefault('v_seat_type', '2nd')
            count = int(ticket_info.setdefault('v_count', 2))
            ticket_info.setdefault('v_age', '_'.join(['-1'] * count))
            ticket_info.setdefault('v_hold_seat', '_'.join(['1'] * count))

        self.ticket_info.update(ticket_info)

    def __str__(self):
        return json.dumps(self.__dict__, ensure_ascii=False)

    @staticmethod
    def parse(s):
        '''
            从json字符串中解析初task
        '''
        if s is None:
            return None

        if s is None or len(s.strip()) == 0:
            return None

        data = None
        try:
            data = json.loads(s)
        except:
            return None

        if data is None:
            return None

        task = Task()
        for k, v in data.items():
            task.__dict__[k] = v

        task.task_data = s

        return task


class RequiredRoom(object):
    __slots__ = ('adult', 'child', 'child_age')

    def __init__(self, value={'adult': 2, 'child': 0, 'child_age': []}, default_child_age=6):
        self.adult = value.get('adult', 2)
        self.child = value.get('child', 0)
        self.child_age = value.get('child_age', [default_child_age] * self.child)

def creat_hotelParams(content):
    """
    酒店例行任务解析
    """
    _,adult,nights,check_in = content.split('&')
    rooms = [{'adult':int(adult)}]
    return HotelParams(value={'check_in': check_in, 'nights': int(nights), 'rooms': rooms})

class HotelParams(object):
    __slots__ = ('check_in', 'check_out', 'night', 'rooms_required', 'rooms_count', 'adult', 'child')

    def __init__(self, value={'check_in': '20170512', 'nights': 1, 'rooms': []}):
        self.check_in = datetime.datetime.strptime(value['check_in'], TASK_DATE_FORMAT)
        self.night = value.get('nights', 1)
        self.check_out = self.__init_check_out(self.check_in, self.night)
        self.rooms_count = 0
        self.adult = 0
        self.child = 0
        self.rooms_required = self.__init_rooms_required(value.get('rooms', []))
        self.__init_rooms_info()

    def __init_check_out(self, check_in, nights):
        return check_in + datetime.timedelta(days=nights)

    def __init_rooms_required(self, rooms):
        ps = []
        for r in rooms:
            ps.append(RequiredRoom(value=r))
        if not ps:
            ps.append(RequiredRoom())
        return ps

    def __init_rooms_info(self):
        for r in self.rooms_required:
            self.adult += r.adult
            self.child += r.child
            self.rooms_count += 1

    def format_check_in(self, ft):
        return self.check_in.strftime(ft)

    def format_check_out(self, ft):
        return self.check_out.strftime(ft)


DEFAULT_HOTEL_PARAM = HotelParams()

if __name__ == '__main__':
    print HotelParams().format_check_in('%Y')
    print [1] * 0
