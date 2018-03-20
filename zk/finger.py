# -*- coding: utf-8 -*-
class Finger(object):
    def __init__(self, size, uid, fid, valid, template):
        self.size = size
        self.uid = uid
        self.fid = fid
        self.valid = valid
        self.template = template

    def __str__(self):
        return "<Finger> [u:%i, fid:%i, size:%i ]" %  (self.uid, self.fid, self.size)

    def __repr__(self):
        return "<Finger> [u:%i, fid:%i, size:%i ]" %  (self.uid, self.fid, self.size)
