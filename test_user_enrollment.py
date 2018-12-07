# -*- coding: utf-8 -*-
import sys

from zk import ZK, const

sys.path.append("zk")

conn = None
zk = ZK('192.168.1.201', port=4370, timeout=5)

try:
  conn = zk.connect()
  conn.disable_device()
  zk.set_user(26, 'Shubhamoy Chakrabarty', 0, '', '1', '26')
  zk.enroll_user('26')
  conn.enable_device()
except Exception, e:
    print "Process terminate : {}".format(e)
finally:
    if conn:
        conn.disconnect()