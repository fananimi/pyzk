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
zk = ZK('192.168.2.201', port=4370)
try:
    conn = zk.connect()
    #conn.enroll_user(uid=1)
    for template in conn.get_templates():
        print ("Size     : %s" % template.size)
        print ("UID      : %s" % template.uid)
        print ("FID      : %s"% template.fid)
        print ("Valid    : %s" % template.valid)
        print ("Template : %s" % template.json_pack())
        print ("Mark     : %s" % template.mark)
except Exception as e:
    print ("Process terminate : {}".format(e))
finally:
    if conn:
        conn.disconnect()
