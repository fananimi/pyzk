# pyzk

pyzk is an unofficial library of zksoftware the fingerprint attendance machine.

# Installation

[![Build Status](https://travis-ci.org/kurenai-ryu/pyzk.svg?branch=master)](https://travis-ci.org/kurenai-ryu/pyzk)

replace original pyzk, if it was installed

```sh
pip install -U git+https://github.com/kurenai-ryu/pyzk.git
```

or using pipenv:

```sh
pipenv install git+https://gith.com/kurenai-ryu/pyzk#egg=pyzk
```

or clone and execute:

```sh
python setup.py install
```

or in your project, append the path of this project

```python
import sys
import os
sys.path.insert(1,os.path.abspath("./pyzk"))
from zk import ZK, const
```

# Documentation

Complete documentation of the original project can be found at [Readthedocs](http://pyzk.readthedocs.io/en/latest/ "pyzk's readthedocs") .

# Api Usage

Just create a ZK object and you will be ready to call api.

* Basic Usage
```python
from zk import ZK, const

conn = None
zk = ZK('192.168.1.201', port=4370, timeout=5, password=0, force_udp=False, ommit_ping=False)
try:
    print ('Connecting to device ...')
    conn = zk.connect()
    print ('Disabling device ...')
    conn.disable_device()
    print ('Firmware Version: : {}'.format(conn.get_firmware_version()))
    # print '--- Get User ---'
    users = conn.get_users()
    for user in users:
        privilege = 'User'
        if user.privilege == const.USER_ADMIN:
            privilege = 'Admin'

        print ('- UID #{}'.format(user.uid))
        print ('  Name       : {}'.format(user.name))
        print ('  Privilege  : {}'.format(privilege))
        print ('  Password   : {}'.format(user.password))
        print ('  Group ID   : {}'.format(user.group_id))
        print ('  User  ID   : {}'.format(user.user_id))

    print ("Voice Test ...")
    conn.test_voice()
    print ('Enabling device ...')
    conn.enable_device()
except Exception as e:
    print ("Process terminate : {}".format(e))
finally:
    if conn:
        conn.disconnect()
```

* Connect/Disconnect

```python
conn = zk.connect()
conn.disconnect()
```

* Disable/Enable Connected Device

```python
conn.disable_device()
conn.enable_device()
```

* Get and Set Time

```python
from datetime import datetime

zktime = conn.get_time()
print zktime

newtime = datetime.today()
conn.set_time(newtime)
```


* Ger Firmware Version and extra information

```python
conn.get_firmware_version()
conn.get_serialnumber()
conn.get_platform()
conn.get_device_name()
conn.get_face_version()
conn.get_fp_version()
conn.get_extend_fmt()
conn.get_user_extend_fmt()
conn.get_face_fun_on()
conn.get_compat_old_firmware()
conn.get_network_params()
conn.get_mac()
conn.get_pin_width()
```

* Get Device use and free Space

```python
conn.read_sizes()
print(conn)
#also:
conn.users
conn.fingers
conn.records
conn.users_cap
conn.fingers_cap
conn.records_cap
```

* User Operation

```python
# Create user
conn.set_user(uid=1, name='Fanani M. Ihsan', privilege=const.USER_ADMIN, password='12345678', group_id='', user_id='123', card=0)
# Get all users (will return list of User object)
users = conn.get_users()
# Delete User
conn.delete_user(uid=1)
```
there is also an `enroll_user()` (but it doesn't work with some tcp ZK8 devices)

* Fingerprints

```python
# Get  a single Fingerprint (will return a Finger object)
template = conn.get_user_template(uid=1, temp_id=0) #temp_id is the finger to read 0~9
# Get all fingers from DB (will return a list of Finger objects)
fingers = conn.get_templates()

# to restore a finger, we need to assemble with the corresponding user
# pass a User object and a list of finger (max 10) to save

conn.save_user_template(user, [fing1 ,fing2])

* Remote Fingerprint Enrollment
```
zk.enroll_user('23')
```


* Attendance Record
```python
# Get attendances (will return list of Attendance object)
attendances = conn.get_attendance()
# Clear attendances record
conn.clear_attendance()
```

* Test voice

```python
conn.test_voice(index=10) # beep or chirp
```

* Device Maintenance

```python
# shutdown connected device
conn.power_off()
# restart connected device
conn.restart()
# clear buffer
conn.free_data()
```

* Live Capture!

```python
# live capture! (timeout at 10s)
for attendance in conn.live_capture():
    if attendance is None:
        # implement here timeout logic
        pass
    else:
        print (attendance) # Attendance object
    #
    #if you need to break gracefully just set
    #   conn.end_live_capture = True
    #
    # On interactive mode,
    # use Ctrl+C to break gracefully
    # this way it restores timeout
    # and disables live capture
```

**Test Machine**

```sh
usage: ./test_machine.py [-h] [-a ADDRESS] [-p PORT] [-T TIMEOUT] [-P PASSWORD]
                         [-f] [-t] [-r] [-u] [-l] [-D DELETEUSER] [-A ADDUSER]
                         [-E ENROLLUSER] [-F FINGER]

ZK Basic Reading Tests

optional arguments:
  -h, --help            show this help message and exit
  -a ADDRESS, --address ADDRESS
                        ZK device Address [192.168.1.201]
  -p PORT, --port PORT  ZK device port [4370]
  -T TIMEOUT, --timeout TIMEOUT
                        Default [10] seconds (0: disable timeout)
  -P PASSWORD, --password PASSWORD
                        Device code/password
  -b, --basic           get Basic Information only. (no bulk read, ie: users)
  -f, --force-udp       Force UDP communication
  -v, --verbose         Print debug information
  -t, --templates       Get templates / fingers (compare bulk and single read)
  -tr, --templates-raw  Get raw templates (dump templates)
  -r, --records         Get attendance records
  -u, --updatetime      Update Date/Time
  -l, --live-capture    Live Event Capture
  -o, --open-door       Open door

  -D DELETEUSER, --deleteuser DELETEUSER
                        Delete a User (uid)
  -A ADDUSER, --adduser ADDUSER
                        Add a User (uid) (and enroll)
  -E ENROLLUSER, --enrolluser ENROLLUSER
                        Enroll a User (uid)
  -F FINGER, --finger FINGER
                        Finger for enroll (fid=0)

```

**Backup/Restore (Users and fingers only!!!)** *(WARNING! destructive test! do it at your own risk!)*

```sh
usage: ./test_backup_restore.py [-h] [-a ADDRESS] [-p PORT] [-T TIMEOUT]
                              [-P PASSWORD] [-f] [-v] [-r]
                              [filename]

ZK Basic Backup/Restore Tool

positional arguments:
  filename              backup filename (default [serialnumber].bak)

optional arguments:
  -h, --help            show this help message and exit
  -a ADDRESS, --address ADDRESS
                        ZK device Address [192.168.1.201]
  -p PORT, --port PORT  ZK device port [4370]
  -T TIMEOUT, --timeout TIMEOUT
                        Default [10] seconds (0: disable timeout)
  -P PASSWORD, --password PASSWORD
                        Device code/password
  -f, --force-udp       Force UDP communication
  -v, --verbose         Print debug information
  -E, --erase           clean the device after writting backup!
  -r, --restore         Restore from backup
  -c, --clear-attendance
                        On Restore, also clears the attendance [default keep
                        attendance]
```

to restore on a different device, make sure to specify the `filename`. on restoring, it asks for the serial number of the destination device (to make sure it was correct, as it deletes all data) WARNING. there is no way to restore attendance data, you can keep it or clear it, but once cleared, there is no way to restore it. 

# Compatible devices

```
Firmware Version : Ver 6.21 Nov 19 2008
Platform : ZEM500
DeviceName : U580

Firmware Version : Ver 6.60 Oct 29 2012
Platform : ZEM800_TFT
DeviceName : iFace402/ID

Firmware Version : Ver 6.60 Dec 27 2014
Platform : ZEM600_TFT
DeviceName : iFace800/ID

Firmware Version : Ver 6.60 Mar 18 2013
Platform : ZEM560
DeviceName : MA300

Firmware Version : Ver 6.60 Dec 1 2010
Platform : ZEM510_TFT
DeviceName : T4-C

Firmware Version : Ver 6.60 Apr 9 2010
Platform : ZEM510_TFT
DeviceName : T4-C

Firmware Version : Ver 6.60 Mar 18 2011
Platform : ZEM600_TFT
DeviceName : iClock260

Firmware Version : Ver 6.60 Nov 6 2017 (remote tested with correct results)
Platform : ZMM220_TFT
DeviceName : (unknown device) (broken info but at least the important data was read)

Firmware Version : Ver 6.60 Jun 9 2017
Platform : JZ4725_TFT
DeviceName : K20 (latest checked correctly!)
```



### Latest tested (not really confirmed)

```
Firmware Version : Ver 6.60 Jun 16 2015
Platform : JZ4725_TFT
DeviceName : iClock260

Firmware Version : Ver 6.60 Jun 16 2015
Platform : JZ4725_TFT
DeviceName : K14 (not tested, but same behavior like the other one)



Firmware Version : Ver 6.60 Jun 5 2015
Platform : ZMM200_TFT
DeviceName : iClock3000/ID (Active testing! latest fix)

Firmware Version : Ver 6.70 Jul 12 2013
Platform : ZEM600_TFT
DeviceName : iClock880-H/ID (Active testing! latest fix)
```

### Not Working (needs more tests, more information)

```
Firmware Version : Ver 6.4.1 (build 99) (display version 2012-08-31)
Platform : 
DeviceName : iClock260 (no capture data - probably similar problem as the latest TESTED)
```

If you have another version tested and it worked, please inform me to update this list!

# Todo

* Create better documentation
* ~~Finger template downloader & uploader~~
* HTTP Rest api
* ~~Create real time api (if possible)~~
* and much more ...
