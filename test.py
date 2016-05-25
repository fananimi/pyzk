# -*- coding: utf-8 -*-
import sys
from zk import const
sys.path.append("zk")

import zk

zk = zk.ZK('192.168.1.201')
print 'Connecting to device ...'
conn = zk.connect()
if conn.get('status'):
    print conn
    print zk.disable_device()
    print 'Firmware Version: : {}'.format(zk.get_firmware_version())
    # Load test create 2000 users
    for i in range(1, 2000+1):
        privilege = const.USER_DEFAULT
        if i == 1:
            privilege = const.USER_ADMIN
        print zk.set_user(uid=i, name='user #{}'.format(i), privilege=privilege, password='123456', group_id='', user_id='{}'.format(i))
    # print 'Restarting device'
    # print zk.restart()
    # print 'Turning off device'
    # print zk.power_off()
#     # users = zk.get_users()
#     # if users:
#     #     for uid in users:        
#     #         if users[uid][2] == 14:
#     #             level = 'Admin'
#     #         else:
#     #             level = 'User'
#     #         print "[UID %d]: ID: %s, Name: %s, Level: %s, Password: %s" % ( uid, users[uid][0], users[uid][1], level, users[uid][3]  )

    print zk.test_voice()
    print zk.enable_device()
    print 'Disconnecting to device ...'
    print zk.disconnect()
#     if status:
#         print 'Disonnected !'
#     else:
#         print 'Disconnecting Error: {}'.format(message)
else:
    print 'Connecting Error: {}'.format(conn.get('message'))

