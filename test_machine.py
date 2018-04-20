# -*- coding: utf-8 -*-
import sys
import argparse

from zk import ZK, const

sys.path.append("zk")

conn = None


parser = argparse.ArgumentParser(description='ZK Basic Reading Tests')
parser.add_argument('-a', '--address', 
                    help='ZK device Addres [192.168.1.201]', default='192.168.1.201')
parser.add_argument('-p', '--port', type=int,
                    help='device port', default=4370)
parser.add_argument('-T', '--timeout', type=int,
                    help='timeout', default=60)
parser.add_argument('-P', '--password', type=int,
                    help='Device code/password', default=0)
parser.add_argument('-f', '--firmware', type=int,
                    help='test firmware', default=8)
parser.add_argument('-t', '--templates', action="store_true",
                    help='get templates')
parser.add_argument('-r', '--records', action="store_true",
                    help='get records')

args = parser.parse_args()

zk = ZK(args.address, port=args.port, timeout=args.timeout, password=args.password, firmware=args.firmware)
try:
    print 'Connecting to device ...'
    conn = zk.connect()
    print 'Disabling device ...'
    conn.disable_device()
    conn.read_sizes()
    print conn
    print 'Firmware Version: : {}'.format(conn.get_firmware_version())
    print 'Platform: %s' % conn.get_platform()
    print 'DeviceName: %s' % conn.get_device_name()
    print 'Pin Width: %i' % conn.get_pin_width()
    print 'Serial Number: %s' % conn.get_serialnumber()
    print 'MAC: %s' % conn.get_mac()
    print ''
    print '--- Get User ---'
    users = conn.get_users()
    for user in users:
        privilege = 'User'
        if user.privilege == const.USER_ADMIN:
            privilege = 'Admin'

        print '-> UID #{:<8}       Name    : {:<8} Privilege : {}'.format(user.uid, user.name, privilege)
        print '   Group ID : {:<8} User ID : {:<8} Password  : {:<8} Card : {}'.format(user.group_id, user.user_id, user.password, user.card)
        print ''
    print "Voice Test ..."
    conn.test_voice(10)
    if args.templates:
        print "Read Templates..."
        templates = conn.get_templates()
        for tem in templates:
            print tem
    if args.records:
        print "Read Records..."
        attendance = conn.get_attendance()
        for att in attendance:
            print "ATT: uid:{:>3}, t: {}".format(att.uid, att.timestamp)
    print 'Enabling device ...'
    conn.enable_device()
except Exception, e:
    print "Process terminate : {}".format(e)
finally:
    if conn:
        conn.disconnect()
