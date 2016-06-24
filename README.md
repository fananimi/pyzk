# pyzk

pyzk is an unofficial library of zksoftware the fingerprint attendance machine.

# Installation

[![Build Status](https://travis-ci.org/fananimi/pyzk.svg?branch=master)](https://travis-ci.org/fananimi/pyzk)

`pip install pyzk`

# Documentation

Complete documentation can be found at [Readthedocs](http://pyzk.readthedocs.io/en/latest/ "pyzk's readthedocs") .

# Api Usage

Create an ZK instnace and you will ready to call api.

* Basic Usage
```
from zk import ZK, const

sys.path.append("zk")

conn = None
zk = ZK('192.168.1.10', port=4370, timeout=5)
try:
    print 'Connecting to device ...'
    conn = zk.connect()
    print 'Disabling device ...'
    conn.disable_device()
    print 'Firmware Version: : {}'.format(conn.get_firmware_version())
    # print '--- Get User ---'
    users = conn.get_users()
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

    print "Voice Test ..."
    conn.test_voice()
    print 'Enabling device ...'
    conn.enable_device()
except Exception, e:
    print "Process terminate : {}".format(e)
finally:
    if conn:
        conn.disconnect()
```

* Connect/Disconnect

```
conn = zk.connect()
conn.disconnect()
```

* Disable/Enable Connected Device

```
conn.disable_device()
conn.enable_device()
```

* Ger Firmware Version

```
conn.get_firmware_version()
```

* User Operation

```
# Create user
conn.set_user(uid=1, name='Fanani M. Ihsan', privilege=const.USER_ADMIN, password='12345678', group_id='', user_id='123')
# Get all users (will return list of User object)
users = conn.get_users()
# Delete User
conn.delete_user(uid=1)
```

* Attendance Record
```
# Get attendances (will return list of Attendance object)
attendances = conn.get_attendance()
# Clear attendances record
conn.clear_attendance()
```

* Test voice

```
conn.test_voice()
```

* Device Maintenance

```
# shutdown connected device
conn.power_off()
# restart connected device
conn.restart()
```

# Related Project

* [zkcluster](https://github.com/fananimi/zkcluster/ "zkcluster project") is a django apps to manage multiple fingerprint devices.

* [Driji](https://github.com/fananimi/driji/ "Driji project") is an attendance apps based fingerprint for school

# Todo

* Create better documentation
* Finger template downloader & uploader
* HTTP Rest api
* Create real time api (if possible)
* and much more ...
