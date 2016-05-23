# -*- coding: utf-8 -*-
import sys
sys.path.append("zk")

import zk

zk = zk.ZK('192.168.1.201')
status, message = zk.connect()
if status:
    print 'Firmware Version: : {}'.format(zk.get_firmware_version())
    users = zk.get_users()
    if users:
        for uid in users:        
            if users[uid][2] == 14:
                level = 'Admin'
            else:
                level = 'User'
            print "[UID %d]: ID: %s, Name: %s, Level: %s, Password: %s" % ( uid, users[uid][0], users[uid][1], level, users[uid][3]  )

    print zk.disconnect()
else:
    print message
