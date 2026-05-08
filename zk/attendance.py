# -*- coding: utf-8 -*-
class Attendance(object):
    def __init__(self, user_id, timestamp, status, punch=0, uid=0):
        self.uid = uid # not really used any more
        self._user_id = user_id
        self._timestamp = timestamp
        self._status = status
        self._punch = punch

    def __str__(self):
        return '<Attendance>: {} : {} ({}, {})'.format(self._user_id, self._timestamp,
                                                       self._status, self._punch)

    def __repr__(self):
        return '<Attendance>: {} : {} ({}, {})'.format(self._user_id, self._timestamp,
                                                       self._status, self._punch)

    def __call__(self):
        return self._user_id, self._timestamp, self._status, self._punch

    @property
    def user_id(self):
        return self._user_id

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def status(self):
        return self._status

    @property
    def punch(self):
        return self._punch
