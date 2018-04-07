# -*- coding: utf-8 -*-
from struct import pack #, unpack
class User(object):

    def __init__(self, uid, name, privilege, password='', group_id='', user_id='', card=0):
        self.uid = uid
        self.name = name
        self.privilege = privilege
        self.password = password
        self.group_id = group_id
        self.user_id = user_id
        self.card = card # 64 int to 40 bit int
    def repack29(self): # with 02 for zk6 (size 29)
        return pack("<BHB5s8s5sBhI", 2, self.uid, self.privilege, self.password, self.name, pack("Q", self.card), int(self.group_id), 0, int(self.user_id))

    def __str__(self):
        return '<User>: {}'.format(self.name)

    def __repr__(self):
        return '<User>: {}'.format(self.name)
