# -*- coding: utf-8 -*-
class User(object):

    def __init__(self, uid, name, privilege, password='', group_id='', user_id='', card=0):
        self.uid = uid
        self.name = name
        self.privilege = privilege
        self.password = password
        self.group_id = group_id
        self.user_id = user_id
        self.card = card

    def __str__(self):
        return '<User>: {}'.format(self.name)

    def __repr__(self):
        return '<User>: {}'.format(self.name)
