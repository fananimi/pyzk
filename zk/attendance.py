# -*- coding: utf-8 -*-
class Attendance(object):
    def __init__(self, uid, user_id, timestamp, status):
        self.uid = uid
        self.user_id = user_id
        self.timestamp = timestamp
        self.status = status

    def __str__(self):
        return '<Attendance>: {}'.format(self.user_id)

    def __repr__(self):
        return '<Attendance>: {}'.format(self.user_id)
