# -*- coding: utf-8 -*-
import sys
from time import sleep
from zk import ZK, const

sys.path.append("zk")

conn = None
zk = ZK('192.168.1.201', port=4370, timeout=5)
try:
    print 'Connecting to device ...'
    conn = zk.connect()
    print 'Disabling device ...'
    conn.disable_device()
    print 'Firmware Version: : {}'.format(conn.get_firmware_version())
    for i in range(0,65):
        print "test_voice, %i" % i
        zk.test_voice(i)
        sleep(3)
    print 'Enabling device ...'
    conn.enable_device()
except Exception, e:
    print "Process terminate : {}".format(e)
finally:
    if conn:
        conn.disconnect()
