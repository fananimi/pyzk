# -*- coding: utf-8 -*-
import sys
sys.path.append("zk")

import zk

zk = zk.ZK('192.168.1.201')
print zk.connect()
print zk.disconnect()