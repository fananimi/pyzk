#!/usr/bin/env python2
# # -*- coding: utf-8 -*-
import sys
import traceback
import argparse
import time
import datetime

sys.path.append("zk")

from zk import ZK, const
from zk.attendance import Attendance
from zk.exception import ZKErrorResponse, ZKNetworkError
from zk.user import User
from zk.finger import Finger

conn = None


parser = argparse.ArgumentParser(description='ZK Basic Reading Tests')
parser.add_argument('-a', '--address', 
                    help='ZK device Addres [192.168.1.201]', default='192.168.1.201')
parser.add_argument('-p', '--port', type=int,
                    help='device port', default=4370)
parser.add_argument('-T', '--timeout', type=int,
                    help='timeout', default=10)
parser.add_argument('-P', '--password', type=int,
                    help='Device code/password', default=0)
parser.add_argument('-f', '--force-udp', action="store_true",
                    help='Force UDP communication')
parser.add_argument('-t', '--templates', action="store_true",
                    help='get templates')
parser.add_argument('-r', '--records', action="store_true",
                    help='get records')
parser.add_argument('-u', '--updatetime', action="store_true",
                    help='Update Date / Time')
parser.add_argument('-D', '--deleteuser', type=int,
                    help='Delete a User', default=0)
parser.add_argument('-A', '--adduser', type=int,
                    help='Add a User', default=0)
parser.add_argument('-F', '--finger', type=int,
                    help='Finger for register', default=0)

args = parser.parse_args()

zk = ZK(args.address, port=args.port, timeout=args.timeout, password=args.password, force_udp=args.force_udp) # , firmware=args.firmware
try:
    print 'Connecting to device ...'
    conn = zk.connect()
    print 'Disabling device ...'
    conn.disable_device()
    fmt = conn.get_extend_fmt()
    print 'ExtendFmt        : {}'.format(fmt)
    now = datetime.datetime.today().replace(microsecond=0)
    if args.updatetime:
        print '--- Updating Time---'
        conn.set_time(now)
    zk_time = conn.get_time()
    dif = abs(zk_time - now).total_seconds()
    print 'Time             : {}'.format(zk_time)
    if dif > 120:
        print("WRN: TIME IS NOT SYNC!!!!!! (local: %s)" % now)
    print 'Firmware Version : {}'.format(conn.get_firmware_version())
    print 'Platform         : %s' % conn.get_platform()
    print 'DeviceName       : %s' % conn.get_device_name()
    print 'Pin Width        : %i' % conn.get_pin_width()
    print 'Serial Number    : %s' % conn.get_serialnumber()
    print 'MAC: %s' % conn.get_mac()
    print ''
    print '--- sizes & capacity ---'
    conn.read_sizes()
    print conn
    print ''
    print '--- Get User ---'
    users = conn.get_users()
    max_uid = 0
    prev = None
    if not args.deleteuser:
        for user in users:
            privilege = 'User'
            if user.uid > max_uid:
                max_uid = user.uid
            privilege = 'User' if user.privilege == const.USER_DEFAULT else 'Admin-%s' % user.privilege
            print '-> UID #{:<5} Name     : {:<27} Privilege : {}'.format(user.uid, user.name, privilege)
            print '              Group ID : {:<8} User ID : {:<8} Password  : {:<8} Card : {}'.format(user.group_id, user.user_id, user.password, user.card)
            #print len (user.repack73()), user.repack73().encode('hex')
            #print ''
            if args.adduser and user.uid == args.adduser:
                prev = user
    if args.deleteuser:
        print ''
        print '-- Delete User UID#%s ---' % args.deleteuser
        #TODO implementar luego
        conn.delete_user(args.deleteuser)
        users = conn.get_users() #update
        for user in users:
            if user.uid > max_uid:
                max_uid = user.uid
            privilege = 'User' if user.privilege == const.USER_DEFAULT else 'Admin-%s' % user.privilege
            print '-> UID #{:<5} Name     : {:<27} Privilege : {}'.format(user.uid, user.name, privilege)
            print '              Group ID : {:<8} User ID : {:<8} Password  : {:<8} Card : {}'.format(user.group_id, user.user_id, user.password, user.card)
            #print len (user.repack73()), user.repack73().encode('hex')
            #print ''
            if args.adduser and user.uid == args.adduser:
                prev = user

    if args.adduser:
        uid = int(args.adduser)
        if prev:
            user = prev
            privilege = 'User' if user.privilege == const.USER_DEFAULT else 'Admin-%s' % user.privilege
            print ''
            print '--- Modify User %i ---' % user.uid
            print '-> UID #{:<5} Name     : {:<27} Privilege : {}'.format(user.uid, user.name, privilege)
            print '              Group ID : {:<8} User ID : {:<8} Password  : {:<8} Card : {}'.format(user.group_id, user.user_id, user.password, user.card)
            #discard prev
        else:
            print '--- Add new User %i ---' % uid
        name = raw_input('Name       :')
        admin = raw_input('Admin (y/n):')
        privilege = 14 if admin == 'y' else 0
        password = raw_input('Password   :')
        user_id = raw_input('User ID2   :')
        card = int(raw_input('Card       :'))
        if prev:
            conn.delete_user(uid) #borrado previo
        try:
            conn.set_user(uid, name, privilege, password, '', user_id, card)
        except ZKErrorResponse, e:
            print "error: ", e
            #try new format
            zk_user = User(uid, name, privilege, password, '', user_id, card)
            conn.save_user_template(zk_user)
        conn.delete_user_template(uid, args.finger)
        conn.reg_event(0xFFFF) #
        if conn.enroll_user(uid, args.finger):
            conn.test_voice(18) # register ok
        else:
            conn.test_voice(23) # not registered
        conn.refresh_data()
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
        i = 0
        for att in attendance:
            i +=1
            print "ATT {:>6}: uid:{:>3}, t: {}".format(i, att.uid, att.timestamp)
    print ''
    print '--- sizes & capacity ---'
    conn.read_sizes()
    print conn
    print ''
except Exception, e:
    print "Process terminate : {}".format(e)
    print "Error: %s" % sys.exc_info()[0]
    print '-'*60
    traceback.print_exc(file=sys.stdout)
    print '-'*60
finally:
    if conn:
        print 'Enabling device ...'
        conn.enable_device()
        conn.disconnect()
        print ''
