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
    template = conn.get_user_template(uid=1, user_id=1, temp_id=6)
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
