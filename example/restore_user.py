# -*- coding: utf-8 -*-
import os
import sys

CWD = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(CWD)
sys.path.append(ROOT_DIR)

from zk import ZK
from zk.finger import Finger


conn = None
zk = ZK('192.168.1.201', port=4370)
try:
    conn = zk.connect()
    print ("-- Restore Finger Information --")
    user = conn.get_user(1)
    with open('finger_1.bin', 'rb') as my_finger:
        bin = my_finger.read()
        fing1 = Finger(user.uid, 1, True, bin)
        conn.save_user_template(user, [fing1])
except Exception as e:
    print ("Process terminate : {}".format(e))
finally:
    if conn:
        conn.disconnect()
