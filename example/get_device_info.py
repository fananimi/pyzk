# -*- coding: utf-8 -*-
import os
import sys

CWD = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(CWD)
sys.path.append(ROOT_DIR)

from zk import ZK


conn = None
zk = ZK('192.168.2.201', port=4370)
try:
    conn = zk.connect()
    print ("-- Device Information --")
    print ("   Current Time            : %s" % conn.get_time())
    print ("   Firmware Version        : %s" % conn.get_firmware_version())
    print ("   Device Name             : %s" % conn.get_device_name())
    print ("   Serial Number           : %s" % conn.get_serialnumber())
    print ("   Mac Address             : %s" % conn.get_mac())
    print ("   Face Algorithm Version  : %s" % conn.get_face_version())
    print ("   Finger Algorithm        : %s" % conn.get_fp_version())
    print ("   Platform Information    : %s" % conn.get_platform())
    #print (conn.get_extend_fmt())
    #print (conn.get_user_extend_fmt())
    #print (conn.get_face_fun_on())
    #print (conn.get_compat_old_firmware())
    network_info = conn.get_network_params()
    print ("-- Network Information")
    print ("   IP                      : %s" % network_info.get('ip'))
    print ("   Netmask                 : %s" % network_info.get('mask'))
    print ("   Gateway                 : %s" % network_info.get('gateway'))
    #print (conn.get_pin_width())
    #print (conn.free_data())
    #print (conn.refresh_data())
except Exception as e:
    print ("Process terminate : {}".format(e))
finally:
    if conn:
        conn.disconnect()
