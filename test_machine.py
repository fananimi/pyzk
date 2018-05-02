#!/usr/bin/env python2
# # -*- coding: utf-8 -*-
import sys
import traceback
import argparse
import time
import datetime
from builtins import input

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
parser.add_argument('-l', '--live-capture', action="store_true",
                    help='Live Event Capture')
parser.add_argument('-D', '--deleteuser', type=int,
                    help='Delete a User (uid)', default=0)
parser.add_argument('-A', '--adduser', type=int,
                    help='Add a User (uid)', default=0)
parser.add_argument('-E', '--enrolluser', type=int,
                    help='Enroll a User (uid)', default=0)
parser.add_argument('-F', '--finger', type=int,
                    help='Finger for register', default=0)

args = parser.parse_args()

zk = ZK(args.address, port=args.port, timeout=args.timeout, password=args.password, force_udp=args.force_udp) # , firmware=args.firmware
try:
    print('Connecting to device ...')
    conn = zk.connect()
    print('SDK build=1      : %s' % conn.set_sdk_build_1()) # why?
    print ('Disabling device ...')
    conn.disable_device()
    fmt = conn.get_extend_fmt()
    print ('ExtendFmt        : {}'.format(fmt))
    fmt = conn.get_user_extend_fmt()
    print ('UsrExtFmt        : {}'.format(fmt))
    print ('Face FunOn       : {}'.format(conn.get_face_fun_on()))
    print ('Face Version     : {}'.format(conn.get_face_version()))
    print ('Finger Version   : {}'.format(conn.get_fp_version()))
    print ('Old Firm compat  : {}'.format(conn.get_compat_old_firmware()))
    net = conn.get_network_params()
    print ('IP:{} mask:{} gateway:{}'.format(net['ip'],net['mask'], net['gateway']))
    now = datetime.datetime.today().replace(microsecond=0)
    if args.updatetime:
        print ('--- Updating Time---')
        conn.set_time(now)
    zk_time = conn.get_time()
    dif = abs(zk_time - now).total_seconds()
    print ('Time             : {}'.format(zk_time))
    if dif > 120:
        print("WRN: TIME IS NOT SYNC!!!!!! (local: %s) use command -u to update" % now)
    print ('Firmware Version : {}'.format(conn.get_firmware_version()))
    print ('Platform         : %s' % conn.get_platform())
    print ('DeviceName       : %s' % conn.get_device_name())
    print ('Pin Width        : %i' % conn.get_pin_width())
    print ('Serial Number    : %s' % conn.get_serialnumber())
    print ('MAC: %s' % conn.get_mac())
    print ('')
    print ('--- sizes & capacity ---')
    conn.read_sizes()
    print (conn)
    print ('')
    print ('--- Get User ---')
    users = conn.get_users()
    max_uid = 0
    prev = None
    if not args.deleteuser:
        for user in users:
            privilege = 'User'
            if user.uid > max_uid:
                max_uid = user.uid
            privilege = 'User' if user.privilege == const.USER_DEFAULT else 'Admin-%s' % user.privilege
            print ('-> UID #{:<5} Name     : {:<27} Privilege : {}'.format(user.uid, user.name, privilege))
            print ('              Group ID : {:<8} User ID : {:<8} Password  : {:<8} Card : {}'.format(user.group_id, user.user_id, user.password, user.card))
            #print (len (user.repack73()), user.repack73().encode('hex'))
            #print ('')
            if args.adduser and user.uid == args.adduser:
                prev = user
    if args.deleteuser:
        print ('')
        print ('-- Delete User UID#%s ---' % args.deleteuser)
        #TODO implementar luego
        conn.delete_user(args.deleteuser)
        users = conn.get_users() #update
        for user in users:
            if user.uid > max_uid:
                max_uid = user.uid
            privilege = 'User' if user.privilege == const.USER_DEFAULT else 'Admin-%s' % user.privilege
            print ('-> UID #{:<5} Name     : {:<27} Privilege : {}'.format(user.uid, user.name, privilege))
            print ('              Group ID : {:<8} User ID : {:<8} Password  : {:<8} Card : {}'.format(user.group_id, user.user_id, user.password, user.card))
            #print len (user.repack73()), user.repack73().encode('hex')
            #print ''
            if args.adduser and user.uid == args.adduser:
                prev = user

    if args.adduser:
        uid = int(args.adduser)
        if prev:
            user = prev
            privilege = 'User' if user.privilege == const.USER_DEFAULT else 'Admin-%s' % user.privilege
            print ('')
            print ('--- Modify User %i ---' % user.uid)
            print ('-> UID #{:<5} Name     : {:<27} Privilege : {}'.format(user.uid, user.name, privilege))
            print ('              Group ID : {:<8} User ID : {:<8} Password  : {:<8} Card : {}'.format(user.group_id, user.user_id, user.password, user.card))
            #discard prev
        else:
            print ('--- Add new User %i ---' % uid)
        name = input('Name       :')
        admin = input('Admin (y/N):')
        privilege = 14 if admin == 'y' else 0
        password = input('Password   :')
        user_id = input('User ID2   :')
        card = input('Card       :')
        card = int(card) if card else 0
        if prev:
            conn.delete_user(uid) #borrado previo
        try:
            conn.set_user(uid, name, privilege, password, '', user_id, card)
            args.enrolluser = uid
        except ZKErrorResponse as e:
            print ("error: %s" % e)
            #try new format
            zk_user = User(uid, name, privilege, password, '', user_id, card)
            conn.save_user_template(zk_user)# forced creation
            args.enrolluser = uid
        conn.refresh_data()
    if args.enrolluser:
        uid = int(args.enrolluser)
        print ('--- Enrolling User #{} ---'.format(uid))
        conn.delete_user_template(uid, args.finger)
        conn.reg_event(0xFFFF) #
        if conn.enroll_user(uid, args.finger):
            conn.test_voice(18) # register ok
            tem = conn.get_user_template(uid, args.finger)
            print (tem)
        else:
            conn.test_voice(23) # not registered
        conn.refresh_data()
    print ("Voice Test ...")
    conn.test_voice(10)
    if args.templates:
        print ("Read Templates...")
        templates = conn.get_templates()
        for tem in templates:
            print (tem)
    if args.records:
        print ("Read Records...")
        attendance = conn.get_attendance()
        i = 0
        for att in attendance:
            i +=1
            print ("ATT {:>6}: uid:{:>3}, user_id:{:>8} t: {}, s:{}".format(i, att.uid, att.user_id, att.timestamp, att.status))
    print ('')
    print ('--- sizes & capacity ---')
    conn.read_sizes()
    print (conn)
    if args.live_capture:
        print ('')
        print ('--- Live Capture! (press ctrl+C to break)---') #TODO how?
        counter = 0
        for att in conn.live_capture():
            if att is None:
                #counter += 1 
                print ("timeout {}".format(counter))
            else:
                print ("ATT {:>6}: uid:{:>3}, user_id:{:>8} t: {}, s:{}".format(counter, att.uid, att.user_id, att.timestamp, att.status))
            if counter >= 10:
                conn.end_live_capture = True
        print('')
        print('--- capture End!---')
    print ('')
except Exception as e:
    print ("Process terminate : {}".format(e))
    print ("Error: %s" % sys.exc_info()[0])
    print ('-'*60)
    traceback.print_exc(file=sys.stdout)
    print ('-'*60)
finally:
    if conn:
        print ('Enabling device ...')
        conn.enable_device()
        conn.disconnect()
        print ('ok bye!')
        print ('')
