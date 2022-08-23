# -*- coding: utf-8 -*-
from struct import pack #, unpack
import codecs


class Finger(object):

    def __init__(self, uid, fid, valid, template):
        self.size = len(template) # template only
        self.uid = int(uid)
        self.fid = int(fid)
        self.valid = int(valid)
        self.template = template
        #self.mark = str().encode("hex")
        self.mark = codecs.encode(template[:8], 'hex') + b'...' + codecs.encode(template[-8:], 'hex')

    def repack(self): #full
        return pack("<HHbb%is" % (self.size), self.size+6, self.uid, self.fid, self.valid, self.template)

    def repack_only(self): #only template
        return pack("<H%is" % (self.size), self.size, self.template)

    @staticmethod
    def json_unpack(json):
        return Finger(
            uid=json['uid'],
            fid=json['fid'],
            valid=json['valid'],
            template=codecs.decode(json['template'],'hex')
        )

    def json_pack(self): #packs for json
        return {
            "size": self.size,
            "uid": self.uid,
            "fid": self.fid,
            "valid": self.valid,
            "template": codecs.encode(self.template, 'hex').decode('ascii')
        }

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __str__(self):
        return "<Finger> [uid:{:>3}, fid:{}, size:{:>4} v:{} t:{}]".format(self.uid, self.fid, self.size, self.valid, self.mark)

    def __repr__(self):
        return "<Finger> [uid:{:>3}, fid:{}, size:{:>4} v:{} t:{}]".format(self.uid, self.fid, self.size, self.valid, self.mark)

    def dump(self):
        return "<Finger> [uid:{:>3}, fid:{}, size:{:>4} v:{} t:{}]".format(self.uid, self.fid, self.size, self.valid, codecs.encode(self.template, 'hex'))

