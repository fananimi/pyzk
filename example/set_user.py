# -*- coding: utf-8 -*-
import os
import sys

CWD = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(CWD)
sys.path.append(ROOT_DIR)

from zk import ZK, const
import zk
print (zk.__file__)

conn = None
zk = ZK('192.168.2.201', port=4370, verbose=True)
try:
    conn = zk.connect()
    conn.set_user(uid=1, name='John Doe', privilege=const.USER_DEFAULT, password='12345678', user_id='1')
except Exception as e:
    print ("Process terminate : {}".format(e))
finally:
    if conn:
        conn.disconnect()
