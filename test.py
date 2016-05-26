# -*- coding: utf-8 -*-
import sys
sys.path.append("zk")

import zk
from zk import const

zk = zk.ZK('192.168.1.201')
print 'Connecting to device ...'
conn = zk.connect()
if conn.get('status'):
    print conn
    print 'Disabling device ...'
    print zk.disable_device()
    print 'Firmware Version: : {}'.format(zk.get_firmware_version())
    # Load test create 2000 users
    # for i in range(1, 2000+1):
    #     privilege = const.USER_DEFAULT
    #     if i == 1:
    #         privilege = const.USER_ADMIN
    #     print zk.set_user(uid=i, name='user #{}'.format(i), privilege=privilege, password='12345678', group_id='', user_id='{}'.format(i))
    print '--- Get User ---'
    users = zk.get_users()
    if users.get('status'):
        for user in users.get('data'):
            privilege = 'User'
            if user.privilege == const.USER_ADMIN:
                privilege = 'Admin'

            print '- UID #{}'.format(user.uid)
            print '  Name       : {}'.format(user.name)
            print '  Privilege  : {}'.format(privilege)
            print '  Password   : {}'.format(user.password)
            print '  Group ID   : {}'.format(user.group_id)
            print '  User  ID   : {}'.format(user.user_id)

    print "Voice Test ..."
    print zk.test_voice()
    # print 'Restarting device ...'
    # print zk.restart()
    # print 'Turning off device ...'
    # print zk.power_off()
    print 'Enabling device ...'
    print zk.enable_device()
    print 'Disconnecting to device ...'    
    print zk.disconnect()
else:
    print 'Connecting Error: {}'.format(conn.get('message'))

