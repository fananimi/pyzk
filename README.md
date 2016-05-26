# pyzk

pyzk is unofficial library of zksoftware the fingerprint attendance machine. 

# Ussage

The usage is very simple, just Create new ZK instance and you will ready to call api.

* Basic Ussage
```
import zk

zk = zk.ZK(ip='192.168.1.201', port=4370, timeout=5)
try:
    zk.connect()
    # disable (lock) the device, make sure not activity when process run
    zk.disable_device()

    # Do another task here
    firmware = zk.get_firmware_version()
    print 'Firmware Version: : {}'.format(firmware.get('data'))

    # don't forget to re-enable device
    zk.enable_device()
except Exception, e:
    print "Process terminate : {}".format(e)
finally:
    if zk.is_connect:
        zk.disconnect()

```

* Ger Firmware Version

```
zk.get_firmware_version()
```

* Create User

```
zk.set_user(uid=1, name='Fanani M. Ihsan', privilege=const.USER_ADMIN, password='12345678', group_id='', user_id='123')
```

* Test voice

```
zk.test_voice()
```

* Shutdown Device

```
zk.power_off()
```

* Restart

```
zk.restart()
```