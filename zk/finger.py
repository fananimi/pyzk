# -*- coding: utf-8 -*-
from struct import pack #, unpack
class Finger(object):
    def __init__(self, size, uid, fid, valid, template):
        self.size = size
        self.uid = uid
        self.fid = fid
        self.valid = valid
        self.template = template
    def repack(self):
        return pack("HHbb%is" % (self.size-6), self.size, self.uid, self.fid, self.valid, self.template)

    def __str__(self):
        return "<Finger> [u:%i, fid:%i, size:%i ]" %  (self.uid, self.fid, self.size)

    def __repr__(self):
        return "<Finger> [u:%i, fid:%i, size:%i ]" %  (self.uid, self.fid, self.size)
