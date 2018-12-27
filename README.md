# pyzk

pyzk is an unofficial library of zksoftware (zkteco family) the fingerprint attendance machine.

# Installation

[![Build Status](https://travis-ci.org/fananimi/pyzk.svg?branch=master)](https://travis-ci.org/fananimi/pyzk)

```sh
pip install -U pyzk
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

Complete documentation can be found at [Readthedocs](http://pyzk.readthedocs.io/en/latest/ "pyzk's readthedocs") .

# API Usage

Create the ZK object and you will be ready to call api.

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
# disable (lock) device, ensure no activity while some process run
conn.disable_device()
# re-enable the connected device
conn.enable_device()
```

* Get and Set Time

```python
from datetime import datetime
# get current machine's time
zktime = conn.get_time()
print zktime
# update new time to machine
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
# TODO: add records_cap counter
# conn.records_cap
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

* Fingerprints

```python
# Get  a single Fingerprint (will return a Finger object)
template = conn.get_user_template(uid=1, temp_id=0) #temp_id is the finger to read 0~9
# Get all fingers from DB (will return a list of Finger objects)
fingers = conn.get_templates()

# to restore a finger, we need to assemble with the corresponding user
# pass a User object and a list of finger (max 10) to save
conn.save_user_template(user, [fing1 ,fing2])
```

* Remote Fingerprint Enrollment
```python
zk.enroll_user('1')
# but it doesn't work with some tcp ZK8 devices
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
"""
play test voice:
0 Thank You
1 Incorrect Password
2 Access Denied
3 Invalid ID
4 Please try again
5 Re-enter ID
6 The clock is full
7 The clock is full
8 Duplicate finger
9 Accepted. Thank you
10 beep kuko
11 beep siren
12 -
13 beep bell
/*
**
***
HELP! TRANSLATE TO ENGLISH THE FOLLOWING ITEMS
***
**
*
*/
14 excedido tiempo p esta operacion  /-
15 coloque su dedo de nuevo  /-
16 coloque su dedo por ultima vez  /-
17 ATN numero de tarjeta está repetida  /-
18 proceso de registro correcto *  /-
19 borrado correcto /-
20 Numero de usuario / ponga la caja de ojos
21 ATN se ha llegado al max num usuarios /-
22 verificacion de usuarios /-
23 usuario no registrado /-
24 ATN se ha llegado al num max de registros /-
25 ATN la puerta no esta cerrada /-
26 registro de usuarios /-
27 borrado de usuarios /-
28 coloque su dedo  /-
29 registre la tarjeta de administrador /-
30 0 /-
31 1 /-
32 2 /-
33 3 /-
34 4 /-
35 5 /-
36 6 /-
37 7 /-
38 8 /-
39 9 /-
40 PFV seleccione numero de usuario /-
41 registrar /-
42 operacion correcta /-
43 PFV acerque su tarjeta /-
43 la tarjeta ha sido registrada /-
45 error en operacion /-
46 PFV acerque tarjeta de administracion, p confirmacion /-
47 descarga de fichajes /-
48 descarga de usuarios /-
49 carga de usuarios /-
50 actualizan de firmware /-
51 ejeuctar ficheros de configuracion /-
52 confirmación de clave de acceso correcta /-
53 error en operacion de tclado /-
54 borrar todos los usuarios /-
55 restaurar terminal con configuracion por defecto /-
56 introduzca numero de usuario /-
57 teclado bloqueado /-
58 error en la gestión de la tarjeta  /-
59 establezca una clave de acceso /-
60 pulse el teclado  /-
61 zona de accceso invalida /-
62 acceso combinado invĺlido /-
63 verificación multiusuario /-
64 modo de verificación inválido /-
65 - /-
"""
conn.test_voice(index=0) # will say 'Thank You'
```

* Device Maintenance

```python
# DANGER!!! This command will be erase all data in the device (incude: user, attendance report, and finger database)
conn.clear_data()
# shutdown connected device
conn.poweroff()
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

To restore on a different device, make sure to specify the `filename`. on restoring, it asks for the serial number of the destination device (to make sure it was correct, as it deletes all data) WARNING. there is no way to restore attendance data, you can keep it or clear it, but once cleared, there is no way to restore it. 

# Compatible devices

```
Firmware Version : Ver 6.21 Nov 19 2008
Platform : ZEM500
DeviceName : U580

Firmware Version : Ver 6.60 Apr 9 2010
Platform : ZEM510_TFT
DeviceName : T4-C

Firmware Version : Ver 6.60 Dec 1 2010
Platform : ZEM510_TFT
DeviceName : T4-C

Firmware Version : Ver 6.60 Mar 18 2011
Platform : ZEM600_TFT
DeviceName : iClock260

Platform         : ZEM560_TFT
Firmware Version : Ver 6.60 Feb  4 2012
DeviceName       :

Firmware Version : Ver 6.60 Oct 29 2012
Platform : ZEM800_TFT
DeviceName : iFace402/ID

Firmware Version : Ver 6.60 Mar 18 2013
Platform : ZEM560
DeviceName : MA300

Firmware Version : Ver 6.60 Dec 27 2014
Platform : ZEM600_TFT
DeviceName : iFace800/ID

Firmware Version : Ver 6.60 Nov 6 2017 (remote tested with correct results)
Platform : ZMM220_TFT
DeviceName : (unknown device) (broken info but at least the important data was read)

Firmware Version : Ver 6.60 Jun 9 2017
Platform : JZ4725_TFT
DeviceName : K20 (latest checked correctly!)

Firmware Version : Ver 6.60 Aug 23 2014 
Platform : ZEM600_TFT
DeviceName : VF680 (face device only, but we read the user and attendance list!)
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
