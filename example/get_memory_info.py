# -*- coding: utf-8 -*-
import os
import sys

CWD = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(CWD)
sys.path.append(ROOT_DIR)

from zk import ZK


conn = None
zk = ZK('192.168.2.201', port=4370)
try:
    conn = zk.connect()
    print ("-- Memory Information --")
    conn.read_sizes()
    print ("User        (used/max)  : %s/%s" % (conn.users, conn.users_cap))
    print ("Fingerprint (used/max)  : %s/%s" % (conn.fingers, conn.fingers_cap))
    #print conn.dummy
    #print conn.cards
    #print conn.rec_cap
    #print conn.fingers_av
    #print conn.users_av
    #print conn.rec_av
except Exception as e:
    print ("Process terminate : {}".format(e))
finally:
    if conn:
        conn.disconnect()
