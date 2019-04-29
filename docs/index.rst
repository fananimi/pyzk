.. pyzk documentation master file, created by
   sphinx-quickstart on Fri May 27 00:09:19 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. toctree::
   :hidden:
   :maxdepth: 4
   :caption: Home Page
   :name: index

   topic1
   topic2
   topic3
   topic4
   topic5
   compatible_devices


******************
pyzk Documentation
******************

**pyzk** is an unofficial library of zksoftware (zkzteco family) a biometric attendance machine. It's easy to use and no need to understand how to communicate to device.

.. image:: https://travis-ci.org/fananimi/pyzk.svg?branch=master
    :target: https://travis-ci.org/fananimi/pyzk

Installation
############


You can install from two different options

1. from pypi

  ``$ pip install pyzk``


2. from original repository

Go to `repository <//github.com/fananimi/pyzk>`_ then clone the latest source code by using git, and then just execute the setup.py file.


 ``$ python setup.py install``


Basic Usage
###########

.. code-block:: python

    from zk import ZK, const

    conn = None
    zk = ZK('192.168.1.201', port=4370, timeout=5)
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


Technical Documentation
#######################

We open to everyone to contribute on this project. Please refer `Communication_protocol_manual_CMD.pdf <https://github.com/fananimi/pyzk/blob/master/docs/_static/Communication_protocol_manual_CMD.pdf>`_ before you start writing the code.


Indices and tables
##################

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

