# -*- coding: utf-8 -*-
from struct import pack #, unpack
import codecs
class Finger(object):
    def __init__(self, uid, fid, valid, template):
        self.size = len(template) # template only
        self.uid = uid
        self.fid = fid
        self.valid = valid
        self.template = template
        #self.mark = str().encode("hex")
        self.mark = codecs.encode(template[:6], 'hex')
    def repack(self): #full
        return pack("HHbb%is" % (self.size), self.size+6, self.uid, self.fid, self.valid, self.template)

    def repack_only(self): #only template
        return pack("H%is" % (self.size), self.size+2, self.template)

    def __str__(self):
        return "<Finger> [uid:%i, fid:%i, size:%i v:%i t:%s...]" %  (self.uid, self.fid, self.size, self.valid, self.mark)

    def __repr__(self):
        return "<Finger> [uid:%i, fid:%i, size:%i v:%i t:%s...]" %  (self.uid, self.fid, self.size, self.valid, self.mark) #.encode('hex')
