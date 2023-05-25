# -*- coding: utf-8 -*-
from struct import pack #, unpack
class User(object):
    encoding = 'UTF-8'

    def __init__(self, uid, name, privilege, password='', group_id='', user_id='', card=0):
        self.uid = uid
        self.name = u'{0}'.format(name)
        self.privilege = privilege
        self.password = str(password)
        self.group_id = str(group_id)
        self.user_id = user_id
        self.card = int(card) # 64 int to 40 bit int

    @staticmethod
    def json_unpack(json):
        #validate?
        return User(
            uid=json['uid'],
            name=json['name'],
            privilege=json['privilege'],
            password=json['password'],
            group_id=json['group_id'],
            user_id=json['user_id'],
            card=json['card']
        )

    def repack29(self): # with 02 for zk6 (size 29)
        return pack("<BHB5s8sIxBhI", 2, self.uid, self.privilege, self.password.encode(User.encoding, errors='ignore'), self.name.encode(User.encoding, errors='ignore'), self.card, int(self.group_id) if self.group_id else 0, 0, int(self.user_id))

    def repack73(self): #with 02 for zk8 (size73)
        #password 6s + 0x00 + 0x77
        # 0,0 => 7sx group id, timezone?
        return pack("<BHB8s24sIB7sx24s", 2, self.uid, self.privilege,self.password.encode(User.encoding, errors='ignore'), self.name.encode(User.encoding, errors='ignore'), self.card, 1, str(self.group_id).encode(User.encoding, errors='ignore'), str(self.user_id).encode(User.encoding, errors='ignore'))

    def is_disabled(self):
        return bool(self.privilege & 1)

    def is_enabled(self):
        return not self.is_disabled()

    def usertype(self):
        return (self.privilege  & 0xE)

    def __str__(self):
        return u'<User>: [uid:{}, name:{} user_id:{}]'.format(self.uid, self.name, self.user_id)

    def __repr__(self):
        return u'<User>: [uid:{}, name:{} user_id:{}]'.format(self.uid, self.name, self.user_id)
