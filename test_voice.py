#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys
import argparse

sys.path.append("zk")

from time import sleep
from zk import ZK, const

parser = argparse.ArgumentParser(description='ZK Basic Reading Tests')
parser.add_argument('-a', '--address', 
                    help='ZK device Addres [192.168.1.201]', default='192.168.1.201')
parser.add_argument('-p', '--port', type=int,
                    help='device port [4370]', default=4370)
parser.add_argument('-T', '--timeout', type=int,
                    help='timeout [60]', default=60)
parser.add_argument('-P', '--password', type=int,
                    help='Device code/password', default=0)
parser.add_argument('-f', '--force-udp', action="store_true",
                    help='Force UDP communication')
parser.add_argument('-v', '--verbose', action="store_true",
                    help='Print debug information')
args = parser.parse_args()


conn = None
zk = ZK(args.address, port=args.port, timeout=args.timeout, password=args.password, force_udp=args.force_udp, verbose=args.verbose)
try:
    print ('Connecting to device ...')
    conn = zk.connect()
    print ('Disabling device ...')
    conn.disable_device()
    print ('Firmware Version: : {}'.format(conn.get_firmware_version()))
    for i in range(0,65):
        print ("test_voice, %i" % i)
        zk.test_voice(i)
        sleep(3)
    print ('Enabling device ...')
    conn.enable_device()
except Exception as e:
    print ("Process terminate : {}".format(e))
finally:
    if conn:
        conn.disconnect()
