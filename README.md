# pyzk

pyzk is unofficial library of zksoftware the fingerprint attendance machine.

# Installation

[![Build Status](https://travis-ci.org/fananimi/pyzk.svg?branch=master)](https://travis-ci.org/fananimi/pyzk)

`pip install pyzk`

# Documentation

Complete documentation can be found at [Readthedocs](http://pyzk.readthedocs.io/en/latest/ "pyzk's readthedocs") .

# Api Usage

Create ZK object and you will ready to call api.

* Basic Usage
```
import zk
from zk import const

conn = False
zk = zk.ZK(ip='192.168.1.201', port=4370, timeout=5)
try:
    conn = zk.connect()

    # disable (lock) the device, make sure no activity when process run
    zk.disable_device()

    # Do another task here
    firmware_version = zk.get_firmware_version()
    print 'Firmware Version: : {}'.format(firmware_version)
    users = zk.get_users()
    for user in users:
        privilege = 'User'
        if user.privilege == const.USER_ADMIN:
            privilege = 'Admin'

        print '- UID #{}'.format(user.uid)
        print '  Name       : {}'.format(user.name)
        print '  Privilege  : {}'.format(privilege)
        print '  Password   : {}'.format(user.password)
        print '  Group ID   : {}'.format(user.group_id)
        print '  User  ID   : {}'.format(user.user_id)

    zk.enable_device()
except Exception, e:
    print "Process terminate : {}".format(e)
finally:
    if conn:
        zk.disconnect()

```

* Connect/Disconnect

```
zk.connect()
zk.disconnect()
```

* Disable/Enable Connected Device

```
zk.disable_device()
zk.enable_device()
```

* Ger Firmware Version

```
zk.get_firmware_version()
```

* User Operation

```
# Create user
zk.set_user(uid=1, name='Fanani M. Ihsan', privilege=const.USER_ADMIN, password='12345678', group_id='', user_id='123')
# Get all users (will return list of User object)
users = zk.get_users()
# Delete User
zk.delete_user(uid=1)
```

* Attendance Record
```
# Get attendances (will return list of Attendance object)
attendances = zk.get_attendance()
# Clear attendances record
zk.clear_attendance()
```

* Test voice

```
zk.test_voice()
```

* Device Maintenance

```
# shutdown connected device
zk.power_off()
# restart connected device
zk.restart()
```

# Todo

* Create better documentation
* Finger template downloader & uploader
* HTTP Rest api
* Create real time api (if possible)
* and much more ...
