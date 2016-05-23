# -*- coding: utf-8 -*-
import sys
sys.path.append("zk")

import zk

zk = zk.ZK('192.168.1.201')
status, message = zk.connect()
if status:
    print 'Firmware Version: : {}'.format(zk.get_firmware_version())
    zk.restart()
    print zk.disconnect()
else:
    print message
