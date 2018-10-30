#!/usr/bin/env python2
# # -*- coding: utf-8 -*-
import sys
import traceback
import argparse
import time
import datetime
import codecs
from builtins import input

import json

sys.path.append("zk")

from zk import ZK, const
from zk.user import User
from zk.finger import Finger
from zk.attendance import Attendance
from zk.exception import ZKErrorResponse, ZKNetworkError

class BasicException(Exception):
    pass

conn = None

parser = argparse.ArgumentParser(description='ZK Basic Backup/Restore Tool')
parser.add_argument('-a', '--address',
                    help='ZK device Address [192.168.1.201]', default='192.168.1.201')
parser.add_argument('-p', '--port', type=int,
                    help='ZK device port [4370]', default=4370)
parser.add_argument('-T', '--timeout', type=int,
                    help='Default [10] seconds (0: disable timeout)', default=10)
parser.add_argument('-P', '--password', type=int,
                    help='Device code/password', default=0)
parser.add_argument('-f', '--force-udp', action="store_true",
                    help='Force UDP communication')
parser.add_argument('-v', '--verbose', action="store_true",
                    help='Print debug information')
parser.add_argument('-E', '--erase', action="store_true",
                    help='clean the device after  writting backup!')
parser.add_argument('-r', '--restore', action="store_true",
                    help='Restore from backup')
parser.add_argument('-c', '--clear-attendance', action="store_true",
                    help='On Restore, also clears the attendance [default keep attendance]')
parser.add_argument('filename', nargs='?',
                    help='backup filename (default [serialnumber].bak)', default='')

args = parser.parse_args()

def erase_device(conn, serialnumber, clear_attendance=False):
    """input serial number to corroborate."""
    print ('WARNING! the next step will erase the current device content.')
    print ('Please input the serialnumber of this device [{}] to acknowledge the ERASING!'.format(serialnumber))
    new_serial = input ('Serial Number    : ')
    if new_serial != serialnumber:
        raise BasicException('Serial number mismatch')
    conn.disable_device()
    print ('Erasing device...')
    conn.clear_data()
    if clear_attendance:
        print ('Clearing attendance too!')
        conn.clear_attendance()
    conn.read_sizes()
    print (conn)


zk = ZK(args.address, port=args.port, timeout=args.timeout, password=args.password, force_udp=args.force_udp, verbose=args.verbose)
try:
    print('Connecting to device ...')
    conn = zk.connect()
    serialnumber = conn.get_serialnumber()
    fp_version = conn.get_fp_version()
    print ('Serial Number    : {}'.format(serialnumber))
    print ('Finger Version   : {}'.format(fp_version))
    filename = args.filename if args.filename else "{}.json.bak".format(serialnumber)
    print ('')
    if not args.restore:
        print ('--- sizes & capacity ---')
        conn.read_sizes()
        print (conn)
        print ('--- Get User ---')
        inicio = time.time()
        users = conn.get_users()
        final = time.time()
        print ('Read {} users took {:.3f}[s]'.format(len(users), final - inicio))
        if len(users) == 0:
            raise BasicException("Empty user list, aborting...")
        print ("Read Templates...")
        inicio = time.time()
        templates = conn.get_templates()
        final = time.time()
        print ('Read {} templates took {:.3f}[s]'.format(len(templates), final - inicio))
        #save to file!
        print ('')
        print ('Saving to file {} ...'.format(filename))
        output = open(filename, 'w')
        data = {
            'version':'1.00jut',
            'serial': serialnumber,
            'fp_version': fp_version,
            'users': [u.__dict__ for u in users],
            'templates':[t.json_pack() for t in templates]
            }
        json.dump(data, output, indent=1)
        output.close()
        if args.erase:
            erase_device(conn, serialnumber, args.clear_attendance)
    else:
        print ('Reading file {}'.format(filename))
        infile = open(filename, 'r')
        data = json.load(infile)
        infile.close()
        #compare versions...
        if data['version'] != '1.00jut':
            raise BasicException("file with different version... aborting!")
        if data['fp_version'] != fp_version:
            raise BasicException("fingerprint version mismmatch {} != {} ... aborting!".format(fp_version, data['fp_version']))
        #TODO: check data consistency...
        users = [User.json_unpack(u) for u in data['users']]
        #print (users)
        print ("INFO: ready to write {} users".format(len(users)))
        templates = [Finger.json_unpack(t) for t in data['templates']]
        #print (templates)
        print ("INFO: ready to write {} templates".format(len(templates)))
        erase_device(conn, serialnumber, args.clear_attendance)
        print ('Restoring Data...')
        for u in users:
            #look for Templates
            temps = list(filter(lambda f: f.uid ==u.uid, templates))
            #print ("user {} has {} fingers".format(u.uid, len(temps)))
            conn.save_user_template(u,temps)
        conn.enable_device()
        print ('--- final sizes & capacity ---')
        conn.read_sizes()
        print (conn)
except BasicException as e:
    print (e)
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
