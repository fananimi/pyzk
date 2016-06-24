.. pyzk documentation master file, created by
   sphinx-quickstart on Fri May 27 00:09:19 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

********************************
Welcome to pyzk's documentation!
********************************

pyzk is an unofficial library of zksoftware the fingerprint attendance machine. It's easy to use and no need to understand how to communicate to device. Just create ZK instance and you will ready to use api.

Installation
############

.. image:: https://travis-ci.org/fananimi/pyzk.svg?branch=master
    :target: https://travis-ci.org/fananimi/pyzk

You can install from two different options

1. from pypi

  ``$ pip install pyzk``


2. from original repository

Go to https://github.com/fananimi/pyzk and clone the latest source code by using git, and then just execute the setup.py file.


 ``$ python setup.py install``


Basic Usage
###########

.. code-block:: python

    from zk import ZK, const

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

API Ussage
##########

**Connect/Disconnect**

.. code-block:: python

    conn = zk.connect()
    conn.disconnect()


**Disable/Enable Connected Device**

.. code-block:: python

    conn.disable_device()
    conn.enable_device()


**Ger Firmware Version**

.. code-block:: python

    conn.get_firmware_version()


**User Operation**

.. code-block:: python

    # Create user
    conn.set_user(uid=1, name='Fanani M. Ihsan', privilege=const.USER_ADMIN, password='12345678', group_id='', user_id='123')
    # Get all users (will return list of User object)
    users = conn.get_users()
    # Delete User
    conn.delete_user(uid=1)


**Attendance Record**

.. code-block:: python

    # Get attendances (will return list of Attendance object)
    attendances = conn.get_attendance()
    # Clear attendances record
    conn.clear_attendance()


**Test voice**

.. code-block:: python

    conn.test_voice()


**Device Maintenance**

.. code-block:: python

    # shutdown connected device
    conn.power_off()
    # restart connected device
    conn.restart()


Technical Documentation
#######################

We open to everyone for contribute in this project. Please refer `Communication_protocol_manual_CMD.pdf <https://github.com/fananimi/pyzk/blob/master/docs/_static/Communication_protocol_manual_CMD.pdf>`_ before you starting write your code.

.. toctree::
   :maxdepth: 2


Indices and tables
##################

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
