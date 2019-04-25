#!/usr/bin/env python2
# # -*- coding: utf-8 -*-

import sys
import os
import unittest
import codecs

if sys.version_info[0] < 3:
    from mock import patch, Mock, MagicMock
else:
    from unittest.mock import patch, Mock, MagicMock
    
mock_socket = MagicMock(name='zk.socket')
sys.modules['zk.socket'] = mock_socket
from zk import ZK, const
from zk.base import ZK_helper
from zk.user import User
from zk.finger import Finger
from zk.attendance import Attendance
from zk.exception import ZKErrorResponse, ZKNetworkError

try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp

def dump(obj, nested_level=0, output=sys.stdout):
    spacing = '   '
    if type(obj) == dict:
        print >> output, '%s{' % ((nested_level) * spacing)
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                print >> output, '%s%s:' % ((nested_level + 1) * spacing, k)
                dump(v, nested_level + 1, output)
            else:
                print >> output, '%s%s: %s' % ((nested_level + 1) * spacing, k, v)
        print >> output, '%s}' % (nested_level * spacing)
    elif type(obj) == list:
        print >> output, '%s[' % ((nested_level) * spacing)
        for v in obj:
            if hasattr(v, '__iter__'):
                dump(v, nested_level + 1, output)
            else:
                print >> output, '%s%s' % ((nested_level + 1) * spacing, v)
        print >> output, '%s]' % ((nested_level) * spacing)
    else:
        print >> output, '%s%s' % (nested_level * spacing, obj)


class PYZKTest(unittest.TestCase):
    def setup(self):

        pass

    def tearDown(self):
        pass

    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def test_no_ping(self,helper, socket):
        """ what if ping doesn't response """
        helper.return_value.test_ping.return_value = False #no ping simulated
        #begin
        zk = ZK('192.168.1.201')
        helper.assert_called_with('192.168.1.201', 4370) # called correctly
        self.assertRaisesRegex(ZKNetworkError, "can't reach device", zk.connect)

    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def test_correct_ping(self,helper, socket):
        """ what if ping is ok """
        helper.return_value.test_ping.return_value = True # ping simulated
        helper.return_value.test_tcp.return_value = 1 # helper tcp ok
        socket.return_value.recv.return_value = b''
        #begin
        zk = ZK('192.168.1.201', force_udp=True)
        helper.assert_called_with('192.168.1.201', 4370) # called correctly
        self.assertRaisesRegex(ZKNetworkError, "unpack requires", zk.connect) # no data...?

    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def test_tcp_invalid(self, helper, socket):
        """ Basic tcp invalid """
        helper.return_value.test_ping.return_value = True # ping simulated
        helper.return_value.test_tcp.return_value = 0 # helper tcp ok
        socket.return_value.recv.return_value = b'Invalid tcp data'
        #begin
        zk = ZK('192.168.1.201')
        helper.assert_called_with('192.168.1.201', 4370) # called correctly
        self.assertRaisesRegex(ZKNetworkError, "TCP packet invalid", zk.connect)

    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def test_tcp_connect(self, helper, socket):
        """ Basic connection test """
        helper.return_value.test_ping.return_value = True # ping simulated
        helper.return_value.test_tcp.return_value = 0 # helper tcp ok
        socket.return_value.recv.return_value = codecs.decode('5050827d08000000d007fffc2ffb0000','hex') # tcp CMD_ACK_OK
        #begin
        zk = ZK('192.168.1.201') # already tested
        conn = zk.connect()
        socket.return_value.send.assert_called_with(codecs.decode('5050827d08000000e80317fc00000000', 'hex'))
        conn.disconnect()
        socket.return_value.send.assert_called_with(codecs.decode('5050827d08000000e903e6002ffb0100', 'hex'))

    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def test_force_udp_connect(self, helper, socket):
        """ Force UDP connection test """
        helper.return_value.test_ping.return_value = True # ping simulated
        helper.return_value.test_tcp.return_value = 0 # helper tcp ok
        socket.return_value.recv.return_value = codecs.decode('d007fffc2ffb0000','hex') # tcp CMD_ACK_OK
        #begin
        zk = ZK('192.168.1.201', force_udp=True)
        conn = zk.connect()
        socket.return_value.sendto.assert_called_with(codecs.decode('e80317fc00000000', 'hex'), ('192.168.1.201', 4370))
        conn.disconnect()
        socket.return_value.sendto.assert_called_with(codecs.decode('e903e6002ffb0100', 'hex'), ('192.168.1.201', 4370))

    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def test_udp_connect(self, helper, socket):
        """ Basic auto UDP connection test """
        helper.return_value.test_ping.return_value = True # ping simulated
        helper.return_value.test_tcp.return_value = 1 # helper tcp nope
        socket.return_value.recv.return_value = codecs.decode('d007fffc2ffb0000','hex') # tcp CMD_ACK_OK
        #begin
        zk = ZK('192.168.1.201', force_udp=True)
        conn = zk.connect()
        socket.return_value.sendto.assert_called_with(codecs.decode('e80317fc00000000', 'hex'), ('192.168.1.201', 4370))
        conn.disconnect()
        socket.return_value.sendto.assert_called_with(codecs.decode('e903e6002ffb0100', 'hex'), ('192.168.1.201', 4370))

    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def test_tcp_unauth(self, helper, socket):
        """ Basic unauth test """
        helper.return_value.test_ping.return_value = True # ping simulated
        helper.return_value.test_tcp.return_value = 0 # helper tcp ok
        socket.return_value.recv.side_effect = [
            codecs.decode('5050827d08000000d5075bb2cf450000', 'hex'), # tcp CMD_UNAUTH
            codecs.decode('5050827d08000000d5075ab2cf450100', 'hex') # tcp CMD_UNAUTH
        ]
        #begin
        zk = ZK('192.168.1.201', password=12)
        self.assertRaisesRegex(ZKErrorResponse, "Unauthenticated", zk.connect)
        socket.return_value.send.assert_called_with(codecs.decode('5050827d0c0000004e044e2ccf450100614d323c', 'hex')) # try with password 12

    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def test_tcp_auth(self, helper, socket):
        """ Basic auth test """
        helper.return_value.test_ping.return_value = True # ping simulated
        helper.return_value.test_tcp.return_value = 0 # helper tcp ok
        socket.return_value.recv.side_effect = [
            codecs.decode('5050827d08000000d5075bb2cf450000', 'hex'), # tcp CMD_UNAUTH
            codecs.decode('5050827d08000000d0075fb2cf450100', 'hex'), # tcp CMD_ACK_OK
            codecs.decode('5050827d08000000d00745b2cf451b00', 'hex') # tcp random CMD_ACK_OK TODO: generate proper sequenced response

        ]
        #begin
        zk = ZK('192.168.1.201', password=45)
        conn = zk.connect()
        socket.return_value.send.assert_called_with(codecs.decode('5050827d0c0000004e044db0cf45010061c9323c', 'hex')) #auth with pass 45
        conn.disconnect()
        socket.return_value.send.assert_called_with(codecs.decode('5050827d08000000e90345b6cf450200', 'hex')) #exit

    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def test_tcp_get_size(self, helper, socket):
        """ can read sizes? """
        helper.return_value.test_ping.return_value = True # ping simulated
        helper.return_value.test_tcp.return_value = 0 # helper tcp ok
        socket.return_value.recv.side_effect = [
            codecs.decode('5050827d08000000d0075fb2cf450100', 'hex'), # tcp CMD_ACK_OK
            codecs.decode('5050827d64000000d007a3159663130000000000000000000000000000000000070000000000000006000000000000005d020000000000000f0c0000000000000100000000000000b80b000010270000a0860100b20b00000927000043840100000000000000', 'hex'), #sizes
            codecs.decode('5050827d08000000d00745b2cf451b00', 'hex'), # tcp random CMD_ACK_OK TODO: generate proper sequenced response
        ]
        #begin
        zk = ZK('192.168.1.201') # already tested
        conn = zk.connect()
        socket.return_value.send.assert_called_with(codecs.decode('5050827d08000000e80317fc00000000', 'hex'))
        conn.read_sizes()
        socket.return_value.send.assert_called_with(codecs.decode('5050827d080000003200fcb9cf450200', 'hex'))
        conn.disconnect()
        self.assertEqual(conn.users, 7, "missed user data %s" % conn.users)
        self.assertEqual(conn.fingers, 6, "missed finger data %s" % conn.fingers)
        self.assertEqual(conn.records, 605, "missed record data %s" % conn.records)
        self.assertEqual(conn.users_cap, 10000, "missed user cap %s" % conn.users_cap)
        self.assertEqual(conn.fingers_cap, 3000, "missed finger cap %s" % conn.fingers_cap)
        self.assertEqual(conn.rec_cap, 100000, "missed record cap %s" % conn.rec_cap)

    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def test_tcp_get_users_small_data(self, helper, socket):
        """ can get empty? """
        helper.return_value.test_ping.return_value = True # ping simulated
        helper.return_value.test_tcp.return_value = 0 # helper tcp ok
        socket.return_value.recv.side_effect = [
            codecs.decode('5050827d08000000d0075fb2cf450100', 'hex'), # tcp CMD_ACK_OK
            codecs.decode('5050827d64000000d007a3159663130000000000000000000000000000000000070000000000000006000000000000005d020000000000000f0c0000000000000100000000000000b80b000010270000a0860100b20b00000927000043840100000000000000', 'hex'), #sizes
            codecs.decode('5050827d04020000dd05942c96631500f801000001000e0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003830380000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003832310000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003833350000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003833310000000000000000000000000000000000000000000500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003833320000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003836000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000383432000000000000000000000000000000000000000000','hex'), #DATA directly(not ok)
            codecs.decode('5050827d08000000d00745b2cf451b00', 'hex'), # tcp random CMD_ACK_OK TODO: generate proper sequenced response
            #codecs.decode('5050827d08000000d00745b2cf451b00', 'hex')  # tcp random CMD_ACK_OK TODO: generate proper sequenced response
        ]
        #begin
        zk = ZK('192.168.1.201' )
        conn = zk.connect()
        socket.return_value.send.assert_called_with(codecs.decode('5050827d08000000e80317fc00000000', 'hex'))
        users = conn.get_users()
        socket.return_value.send.assert_called_with(codecs.decode('5050827d13000000df053ca6cf4514000109000500000000000000', 'hex')) #get users
        self.assertEqual(len(users), 7, "incorrect size %s" % len(users))
        #assert one user
        usu = users[3]
        self.assertIsInstance(usu.uid, int, "uid should be int() %s" % type(usu.uid))
        if sys.version_info >= (3, 0):
            self.assertIsInstance(usu.user_id, (str, bytes), "user_id should be str() or bytes() %s" % type(usu.user_id))
        else:
            self.assertIsInstance(usu.user_id, (str, unicode), "user_id should be str() or unicode() %s" % type(usu.user_id))
        self.assertEqual(usu.uid, 4, "incorrect uid %s" % usu.uid)
        self.assertEqual(usu.user_id, "831", "incorrect user_id %s" % usu.user_id)
        self.assertEqual(usu.name, "NN-831", "incorrect uid %s" % usu.name) # generated
        conn.disconnect()

    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def test_tcp_get_users_broken_data(self, helper, socket):
        """ test case for K20 """
        helper.return_value.test_ping.return_value = True # ping simulated
        helper.return_value.test_tcp.return_value = 0 # helper tcp ok
        socket.return_value.recv.side_effect = [
            codecs.decode('5050827d08000000d007d7d758200000','hex'), #ACK Ok
            codecs.decode('5050827d58000000d0074c49582013000000000000000000000000000000000002000000000000000000000000000000000000000000000007000000000000000000000000000000f4010000f401000050c30000f4010000f201000050c30000','hex'),#Sizes
            codecs.decode('5050827d9c000000dd053c87582015009000000001000000000000000000006366756c616e6f0000000000000000000000000000000000000000000000000000000000003130303030316c70000000000000000000000000000000000200000000000000000000726d656e67616e6f0000000000000000000000000000000000','hex'),#DATA112
            codecs.decode('000000000000000000000000323232323232636200000000000000000000000000000000','hex'), #extra data 36
            #codecs.decode('','hex'), #
            codecs.decode('5050827d08000000d00745b2cf451b00', 'hex'),  # CMD_ACK_OK for get_users TODO: generate proper sequenced response
            codecs.decode('5050827d08000000d00745b2cf451b00', 'hex'),  # CMD_ACK_OK for free_data TODO: generate proper sequenced response
            codecs.decode('5050827d08000000d00745b2cf451b00', 'hex'),  # CMD_ACK_OK for exit      TODO: generate proper sequenced response
        ]
        #begin
        zk = ZK('192.168.1.201') #, verbose=True)
        conn = zk.connect()
        socket.return_value.send.assert_called_with(codecs.decode('5050827d08000000e80317fc00000000', 'hex'))
        users = conn.get_users()
        #print (users) #debug
        socket.return_value.send.assert_called_with(codecs.decode('5050827d13000000df05b3cb582014000109000500000000000000', 'hex')) #get users
        self.assertEqual(len(users), 2, "incorrect size %s" % len(users))
        #assert one user
        usu = users[1]
        self.assertIsInstance(usu.uid, int, "uid should be int() %s" % type(usu.uid))
        if sys.version_info >= (3, 0):
            self.assertIsInstance(usu.user_id, (str, bytes), "user_id should be str() or bytes() %s" % type(usu.user_id))
        else:
            self.assertIsInstance(usu.user_id, (str, unicode), "user_id should be str() or unicode() %s" % type(usu.user_id))
        self.assertEqual(usu.uid, 2, "incorrect uid %s" % usu.uid)
        self.assertEqual(usu.user_id, "222222cb", "incorrect user_id %s" % usu.user_id)
        self.assertEqual(usu.name, "rmengano", "incorrect uid %s" % usu.name) # check test case
        conn.disconnect()


    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def test_tcp_get_users_broken_tcp(self, helper, socket):
        """ tst case for https://github.com/fananimi/pyzk/pull/18#issuecomment-406250746 """
        helper.return_value.test_ping.return_value = True # ping simulated
        helper.return_value.test_tcp.return_value = 0 # helper tcp ok
        socket.return_value.recv.side_effect = [
            codecs.decode('5050827d09000000d007babb5c3c100009', 'hex'), # tcp CMD_ACK_OK
            codecs.decode('5050827d58000000d007292c5c3c13000000000000000000000000000000000046000000000000004600000000000000990c0000000000001a010000000000000600000006000000f4010000f401000050c30000ae010000ae010000b7b60000', 'hex'), #sizes
            codecs.decode('5050827d15000000d007a7625c3c150000b4130000b4130000cdef2300','hex'), #PREPARE_BUFFER -> OK 5044
            codecs.decode('5050827d10000000dc050da65c3c1600b4130000f0030000', 'hex'), # read_buffer -> Prepare_data 5044
            codecs.decode('5050827df8030000dd05d05800001600b013000001000e35313437393833004a6573757353616c646976617200000000000000000000000000000001000000000000000035313437393833000000000000000000000000000000000002000e33343934383636004e69657665734c6f70657a00000000000000000000000000000000000100000000000000003334393438363600000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003337333139333600000000000000000000000000', 'hex'), #  DATA 1016 -8 (util 216)
            codecs.decode('0000000100000000000000003734383433330000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003433333939353800000000000000000000000000000000000900000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003333373335313100000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003337373535363100000000000000000000000000000000000b000000', 'hex'), # raw data 256
            codecs.decode('0000000004000e00000000000000000000000000000000000000000000000000000000000000000000000001000000000000000032333338323035000000000000000000000000000000000005000e000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000333632363439300000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000313838343633340000000000000000000000000000000000070000000000000000000000000000000000000000000000000000000000000000000000', 'hex'), #raw data 256
            codecs.decode('00000000000000000000000000000000000000000000000000000000000000000000000100000000000000003131313336333200000000000000000000000000000000000c00000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003130353233383900000000000000000000000000000000000d00000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003135333538333600000000000000000000000000000000000e00000000000000000000000000000000000000000000000000000000000000000000000000000100000000', 'hex'), #raw data 256
            codecs.decode('000000003933313637300000000000000000000000000000', 'hex'), #raw data 24

            codecs.decode('5050827df8030000dd0520b601001600000000000f00003334323931343800000000000000000000000000000000000000000000000000000000000100000000000000003334323931343800000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003139303636393700000000000000000000000000000000001100000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003139333831333500000000000000000000000000', 'hex'), # DATA 1016 -8 (util216
            codecs.decode('00000000120000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000393231303537000000000000000000000000000000000000130000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000333634383739340000000000000000000000000000000000140000323831353732000000000000000000000000000000000000000000000000000000000000010000000000000000323831353732000000000000000000000000000000000000150000000000000000000000000000000000000000000000000000000000000000000000', 'hex'), #raw data 256
            codecs.decode('00000001000000000000000031383133323236000000000000000000000000000000000016000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000035393037353800000000000000000000000000000000000017000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000031363933373232000000000000000000000000000000000018000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000033363430323131000000000000000000000000000000000019000000', 'hex'), #raw data 256
            codecs.decode('00000000000000000000000000000000000000000000000000000000000000000000000100000000000000003331303733390000000000000000000000000000000000001a00000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003433353430393400000000000000000000000000000000001b00000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003338303736333200000000000000000000000000000000001c00000000000000000000000000000000000000000000000000000000000000000000000000000100000000', 'hex'), #raw data 256
            codecs.decode('000000003231333938313700000000000000000000000000', 'hex'), #raw data 24

            codecs.decode('5050827df8030000dd059a2102001600000000001d00000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003333383738313900000000000000000000000000000000001e00000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003439353634363800000000000000000000000000000000001f00000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003832343030300000000000000000000000000000', 'hex'), #DATA 1016 -8 (util 216)
            codecs.decode('00000000200000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000333937373437370000000000000000000000000000000000210000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000343435383038340000000000000000000000000000000000220000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000343430353130390000000000000000000000000000000000230000000000000000000000000000000000000000000000000000000000000000000000', 'hex'), #raw data 256
            codecs.decode('00000001000000000000000033353732363931000000000000000000000000000000000024000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000033363336333832000000000000000000000000000000000025000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000033333232353432000000000000000000000000000000000026000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000039393437303800000000000000000000000000000000000027000000', 'hex'), #raw data 256
            codecs.decode('00000000000000000000000000000000000000000000000000000000000000000000000100000000000000003836333539380000000000000000000000000000000000002800000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003338383736383000000000000000000000000000000000002900000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003739393434350000000000000000000000000000000000002a00000000000000000000000000000000000000000000000000000000000000000000000000000100000000', 'hex'), # raw data 256
            codecs.decode('000000003532313136340000000000000000000000000000', 'hex'), # raw data 24

            codecs.decode('5050827df8030000dd053da903001600000000002b00000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003439373033323400000000000000000000000000000000002c0000000000000000000000000000000000000000000000000000000000000000000000', 'hex'), # DATA 1016 -8 (util 112)
            codecs.decode('0000000100000000000000003134363732353100000000000000000000000000000000002d000e32363635373336006d61726368756b0000000000000000000000000000000000000000000100000000000000003236363537333600000000000000000000000000', 'hex'), # raw data 104
            codecs.decode('000000002e00000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003136383133353200000000000000000000000000000000002f000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000034393633363732000000000000000000000000000000000030000000', 'hex'), # raw data 152
            codecs.decode('00000000000000000000000000000000000000000000000000000000000000000000000100000000000000003337363137373100000000000000000000000000000000003100000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003231353939353100000000000000000000000000000000003200000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003136393734323700000000000000000000000000000000003300000000000000000000000000000000000000000000000000000000000000000000000000000100000000', 'hex'), # raw data 256
            codecs.decode('0000000033373336323437000000000000000000000000000000000034000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000031323930313635000000000000000000000000000000000035000000000000000000000000000000000000000000000000000000', 'hex'), # raw data 128
            codecs.decode('0000000000000000000000010000000000000000333236333636330000000000000000000000000000000000360000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000393031353036000000000000000000000000000000000000370000000000000000000000', 'hex'), # raw data 128
            codecs.decode('0000000000000000000000000000000000000000000000000000000100000000000000003238313732393300000000000000000000000000000000003800000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003437303630333800000000000000000000000000', 'hex'), # raw data 128

            codecs.decode('5050827df8030000dd05037d04001600000000003900000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003136343731353600000000000000000000000000000000003a0000000000000000000000000000000000000000000000000000000000000000000000', 'hex'), # DATA 1016 -8 (util 112)
            codecs.decode('0000000100000000000000003530313435310000000000000000000000000000000000003b00000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003534363236373300000000000000000000000000000000003c00000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003533363730310000000000000000000000000000000000003d00000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003435383033303700000000000000000000000000000000003e000000', 'hex'), # raw data 256
            codecs.decode('00000000000000000000000000000000000000000000000000000000000000000000000100000000000000003136333835333200000000000000000000000000000000003f000e3336323634313900000000000000000000000000000000000000000000000000000000000100000000000000003336323634313900000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003233323331383500000000000000000000000000000000004100000000000000000000000000000000000000000000000000000000000000000000000000000100000000', 'hex'), # raw data 256
            codecs.decode('0000000035323930373337000000000000000000000000000000000042000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000033393839303636000000000000000000000000000000000043000000000000000000000000000000000000000000000000000000', 'hex'), # raw data 128
            codecs.decode('0000000000000000000000010000000000000000343033323930390000000000000000000000000000000000440000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000323034363338380000000000000000000000000000000000450000000000000000000000', 'hex'), # raw data 128
            codecs.decode('0000000000000000000000000000000000000000000000000000000100000000000000003733383730330000000000000000000000000000000000004600000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000003239313836333600000000000000000000000000', 'hex'), # raw data 128

            codecs.decode('5050827d0c000000dd0507fa0500160000000000', 'hex'), #  DATA 12-8 (util 4 ok) and ACK OK!!!

            codecs.decode('5050827d08000000d00745b2cf451b00', 'hex'),  # CMD_ACK_OK for get_users TODO: generate proper sequenced response
            codecs.decode('5050827d08000000d00745b2cf451b00', 'hex'),  # CMD_ACK_OK for free_data TODO: generate proper sequenced response
            codecs.decode('5050827d08000000d00745b2cf451b00', 'hex'),  # CMD_ACK_OK for exit      TODO: generate proper sequenced response
        ]
        #begin
        zk = ZK('192.168.1.201') # , verbose=True)
        conn = zk.connect()
        socket.return_value.send.assert_called_with(codecs.decode('5050827d08000000e80317fc00000000', 'hex'))
        users = conn.get_users()
        #print (users) #debug
        socket.return_value.send.assert_called_with(codecs.decode('5050827d08000000de05aebd5c3c1700', 'hex')) #get users
        self.assertEqual(len(users), 70, "incorrect size %s" % len(users))
        #assert one user
        usu = users[1]
        self.assertIsInstance(usu.uid, int, "uid should be int() %s" % type(usu.uid))
        if sys.version_info >= (3, 0):
            self.assertIsInstance(usu.user_id, (str, bytes), "user_id should be str() or bytes() %s" % type(usu.user_id))
        else:
            self.assertIsInstance(usu.user_id, (str, unicode), "user_id should be str() or unicode() %s" % type(usu.user_id))
        self.assertEqual(usu.uid, 2, "incorrect uid %s" % usu.uid)
        self.assertEqual(usu.user_id, "3494866", "incorrect user_id %s" % usu.user_id)
        self.assertEqual(usu.name, "NievesLopez", "incorrect uid %s" % usu.name) # check test case
        conn.disconnect()

    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def _test_tcp_get_template(self, helper, socket):
        """ can get empty? """
        helper.return_value.test_ping.return_value = True # ping simulated
        helper.return_value.test_tcp.return_value = 0 # helper tcp ok
        socket.return_value.recv.side_effect = [
            codecs.decode('5050827d08000000d0075fb2cf450100', 'hex'), # tcp CMD_ACK_OK
            codecs.decode('5050827d15000000d007acf93064160000941d0000941d0000b400be00', 'hex'), # ack ok with size 7572
            codecs.decode('5050827d10000000dc05477830641700941d000000000100', 'hex'), #prepare data
            codecs.decode('5050827d08000000d00745b2cf451b00', 'hex'), # tcp random CMD_ACK_OK TODO: generate proper sequenced response
            #codecs.decode('5050827d08000000d00745b2cf451b00', 'hex')  # tcp random CMD_ACK_OK TODO: generate proper sequenced response
        ]
        #begin
        zk = ZK('192.168.1.201', verbose=True)
        conn = zk.connect()
        socket.return_value.send.assert_called_with(codecs.decode('5050827d08000000e80317fc00000000', 'hex'))
        templates = conn.get_templates()
        self.assertEqual(len(templates), 6, "incorrect size %s" % len(templates))
        #assert one user
        usu = users[3]
        self.assertIsInstance(usu.uid, int, "uid should be int() %s" % type(usu.uid))
        if sys.version_info >= (3, 0):
            self.assertIsInstance(usu.user_id, (str, bytes), "user_id should be str() or bytes() %s" % type(usu.user_id))
        else:
            self.assertIsInstance(usu.user_id, (str, unicode), "user_id should be str() or unicode() %s" % type(usu.user_id))
        self.assertEqual(usu.uid, 4, "incorrect uid %s" % usu.uid)
        self.assertEqual(usu.user_id, "831", "incorrect user_id %s" % usu.user_id)
        self.assertEqual(usu.name, "NN-831", "incorrect uid %s" % usu.name) # generated
        conn.disconnect()

    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def _test_tcp_get_template_1(self, helper, socket):
        """ cchekc correct template 1 """
        helper.return_value.test_ping.return_value = True # ping simulated
        helper.return_value.test_tcp.return_value = 0 # helper tcp ok
        socket.return_value.recv.side_effect = [
            codecs.decode('5050827d08000000d0075fb2cf450100', 'hex'), # tcp CMD_ACK_OK
            codecs.decode('5050827d10000000dc055558d0983200dc040000f0030000', 'hex'), # tcp PREPARE_DATA 1244
            codecs.decode('5050827df8030000dd0500f4000032004d9853533231000004dbda0408050709ced000001cda69010000008406316adb0c0012062900d000aad221001600390caf001cdbb106240031007e033bdb3b00e9067700850083d42b004300c503f40043dbd6037b005000460ea7db5900910f90009f0012d5e7005c00970a5f006ddb', 'hex'), # DATA (tcp 1016, actual 112?)
            codecs.decode('930fa1009a00560f86db9d00820e86006f007dd3f400ab00a60fcd01b7dbb00b4b00bd0079083adbc00045035d000600c1df7300cc0039049e00dddb380e8c00da00e30dd8dbdc00220e130027004dd9f500e3009d0a6a00e9db26090001ef00ea03c5dbf0002306', 'hex'), #raw data 104
            codecs.decode('d000380028d83400ff00430f6200fbdba70dfb0002016203c5db0201a5044b00c10132d4de0006019f080a000cdab70541000f01fe0f19db1901c902e600dc0198d839002f01360ed80037dabd04d4003301520104da38014f01a100830196d5f5004b015c0411005cdacd03bc67ab8d162b48ad18f7fec7448e448387afa1a3', 'hex'), # raw 128
            codecs.decode('062b37ca3cf9f53c8087f9150926e03335df1b71aedbd0f2', 'hex'), # raw 24
            codecs.decode('b40da90541168df1551f70fc15b51bf26d7d4501bf12915e6485fd966f0ba2072728987dc1018a12ab105ec7aa003508fef08a49b923f3e85e42edf5ea861bd1600d23151787fc78d522f38431883e809f0e4dd2008ecd8ed97670035acf0c763503f27c37ec76d982806986c6016bf952d01e0673820570a87e1a236005ad81', 'hex'), # raw 128
            codecs.decode('7d8734949952bb929d81e5fdbcf99ca0c4886d8c65098c0e9aa6ac81e103c684607951d03b0ce9f0cd785885ad27d4f61bfc5de8bc7411de8d8f5910c518e004e9229304f90f9a891395912680ebc6f4c57fd3fceeb684f7c18ba78107fc2e16073e89f6d6b67fbb', 'hex'), # raw 104
            codecs.decode('fb11e2feb3effd0e5391c61da77176359f7e4d8a0ff3090a01204501c76a19af07002b003ac0042300dbab0113c2fa07c56e02cbc32bc10400a1c31349df0008102d2a04c5120c9b8904008f0810fb0404c20f3a6407006fd709fbecfe0400041529f60304fd1931fb0b006ede0c391bc1c0c0460e00a3210b1a34c2ffffc3fd', 'hex'),  # raw 128
            codecs.decode('980f04832806404a5bc1940505da86292d0f0056f600f925', 'hex'),  # raw 24
            codecs.decode('5c43c243ff06c5733a5d85c7080040473f3d31dd01774d8983c4c000778982750b009459d551c426c3c0170900929b17fba3fc780800376135fefbe0ff1100396aed3b3146265ac0c1ffff15c5357232fffdc0fdc03f3bc141914514003f85e738fdfa2441ff5cc0ff45951504ec7ee9c0fac1fc053dc424c0554affc103c5f8', 'hex'),  # raw 128
            codecs.decode('94f2fd0e00668b06eac1f9b3c3fdc2fd08008388f3ef460a00869e13a56079cf013fb82d22c394c2c619c3c33ac45304c527e19d4d0c008aab1305c0fa1aff6050110083687dc713c396c0c2c1c104c1c6b10f0072b54cc14d83c519c1760e0055b9f8c1f8187486', 'hex'),  # raw 104
            codecs.decode('750d00797ff0fdee593bc1090086781657267f11004cc1375050827df4000000dd0548b10100320038ffc024c2fec4c1c18c05c4fad0013ec54051c2879d00cb56521cc2c204c50fc2e62506008eca1a05fec5250d0072d23dc344c2c45cc10a008bd31a3afefa1a92c0080034e68642c45d0d005bdd376707c08da002008ede', 'hex'),  # raw 128
            codecs.decode('24ffc100e405213306002de78637c4de011de846ff98c100', 'hex'),  # raw 24
            codecs.decode('07283b590300fef3f5f800da10f5494b031000071819061035084365650b14900834c0c1c4c104c1c5a302100e1134c1c01045c83c8806110e2185c22edd11082424fec006ff02cb052834c3c073c910d4eb965b3833ff0bc582cce18d876a051106f337f826c00410013d2b05c200ca003f4cfeff03d56454ccc101', 'hex'),  # raw 124
            codecs.decode('5050827d08000000d007fcf701003200', 'hex'),  # tcp CMD_ACK_OK
            #codecs.decode('5050827d08000000d00745b2cf451b00', 'hex'),  # tcp random CMD_ACK_OK TODO: generate proper sequenced response
        ]
        #begin
        zk = ZK('192.168.1.201', verbose=True)
        conn = zk.connect()
        socket.return_value.send.assert_called_with(codecs.decode('5050827d08000000e80317fc00000000', 'hex'))
        template = conn.get_user_template(14, 1)
        self.assertEqual(template.size, 1243, "incorrect size %s" % template.size)
        self.assertEqual(template.mark, "4d98535332310000...feff03d56454ccc1", "incorrect mark %s" % template.mark)
        self.assertEqual(template.uid, 14, "incorrect uid %s" % template.uid)
        conn.disconnect()

    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def test_tcp_get_template_1f(self, helper, socket):
        """ cchekc correct template 1 fixed"""
        helper.return_value.test_ping.return_value = True # ping simulated
        helper.return_value.test_tcp.return_value = 0 # helper tcp ok
        socket.return_value.recv.side_effect = [
            codecs.decode('5050827d08000000d0075fb2cf450100', 'hex'), # tcp CMD_ACK_OK
            codecs.decode('5050827d10000000dc055558d0983200dc040000f0030000', 'hex'), # tcp PREPARE_DATA 1244
            codecs.decode('5050827df8030000dd0500f4000032004d9853533231000004dbda0408050709ced000001cda69010000008406316adb0c0012062900d000aad221001600390caf001cdbb106240031007e033bdb3b00e9067700850083d42b004300c503f40043dbd6037b005000460ea7db5900910f90009f0012d5e7005c00970a5f006ddb930fa1009a00560f86db9d00820e86006f007dd3f400ab00a60fcd01b7dbb00b4b00bd0079083adbc00045035d000600c1df7300cc0039049e00dddb380e8c00da00e30dd8dbdc00220e130027004dd9f500e3009d0a6a00e9db26090001ef00ea03c5dbf0002306', 'hex'), # DATA (tcp 1016, actual 112 +104
            codecs.decode('d000380028d83400ff00430f6200fbdba70dfb0002016203c5db0201a5044b00c10132d4de0006019f080a000cdab70541000f01fe0f19db1901c902e600dc0198d839002f01360ed80037dabd04d4003301520104da38014f01a100830196d5f5004b015c0411005cdacd03bc67ab8d162b48ad18f7fec7448e448387afa1a3062b37ca3cf9f53c8087f9150926e03335df1b71aedbd0f2', 'hex'), # raw 128 + 24
            codecs.decode('b40da90541168df1551f70fc15b51bf26d7d4501bf12915e6485fd966f0ba2072728987dc1018a12ab105ec7aa003508fef08a49b923f3e85e42edf5ea861bd1600d23151787fc78d522f38431883e809f0e4dd2008ecd8ed97670035acf0c763503f27c37ec76d982806986c6016bf952d01e0673820570a87e1a236005ad817d8734949952bb929d81e5fdbcf99ca0c4886d8c65098c0e9aa6ac81e103c684607951d03b0ce9f0cd785885ad27d4f61bfc5de8bc7411de8d8f5910c518e004e9229304f90f9a891395912680ebc6f4c57fd3fceeb684f7c18ba78107fc2e16073e89f6d6b67fbb', 'hex'), # raw 128 +104
            codecs.decode('fb11e2feb3effd0e5391c61da77176359f7e4d8a0ff3090a01204501c76a19af07002b003ac0042300dbab0113c2fa07c56e02cbc32bc10400a1c31349df0008102d2a04c5120c9b8904008f0810fb0404c20f3a6407006fd709fbecfe0400041529f60304fd1931fb0b006ede0c391bc1c0c0460e00a3210b1a34c2ffffc3fd980f04832806404a5bc1940505da86292d0f0056f600f925', 'hex'),  # raw 128 +24
            codecs.decode('5c43c243ff06c5733a5d85c7080040473f3d31dd01774d8983c4c000778982750b009459d551c426c3c0170900929b17fba3fc780800376135fefbe0ff1100396aed3b3146265ac0c1ffff15c5357232fffdc0fdc03f3bc141914514003f85e738fdfa2441ff5cc0ff45951504ec7ee9c0fac1fc053dc424c0554affc103c5f894f2fd0e00668b06eac1f9b3c3fdc2fd08008388f3ef460a00869e13a56079cf013fb82d22c394c2c619c3c33ac45304c527e19d4d0c008aab1305c0fa1aff6050110083687dc713c396c0c2c1c104c1c6b10f0072b54cc14d83c519c1760e0055b9f8c1f8187486', 'hex'),  # raw 128 +104
            codecs.decode('750d00797ff0fdee593bc1090086781657267f11004cc137', 'hex'),  # raw 24?
            codecs.decode('5050827df4000000dd0548b10100320038ffc024c2fec4c1c18c05c4fad0013ec54051c2879d00cb56521cc2c204c50fc2e62506008eca1a05fec5250d0072d23dc344c2c45cc10a008bd31a3afefa1a92c0080034e68642c45d0d005bdd376707c08da002008ede24ffc100e405213306002de78637c4de011de846ff98c100', 'hex'),  # raw 128-24 (104) +24
            codecs.decode('07283b590300fef3f5f800da10f5494b031000071819061035084365650b14900834c0c1c4c104c1c5a302100e1134c1c01045c83c8806110e2185c22edd11082424fec006ff02cb052834c3c073c910d4eb965b3833ff0bc582cce18d876a051106f337f826c00410013d2b05c200ca003f4cfeff03d56454ccc101', 'hex'),  # raw 124
            codecs.decode('5050827d08000000d007fcf701003200', 'hex'),  # tcp CMD_ACK_OK
            codecs.decode('5050827d08000000d00745b2cf451b00', 'hex'),  # tcp random CMD_ACK_OK TODO: generate proper sequenced response
        ]
        #begin
        zk = ZK('192.168.1.201') #, verbose=True)
        conn = zk.connect()
        socket.return_value.send.assert_called_with(codecs.decode('5050827d08000000e80317fc00000000', 'hex'))
        template = conn.get_user_template(14, 1)
        self.assertEqual(template.size, 1243, "incorrect size %s" % template.size)
        self.assertEqual(template.mark, b"4d98535332310000...feff03d56454ccc1", "incorrect mark %s" % template.mark)
        self.assertEqual(template.uid, 14, "incorrect uid %s" % template.uid)
        conn.disconnect()

    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def test_tcp_get_template_2f(self, helper, socket):
        """ cchekc correct template 2 fixed"""
        helper.return_value.test_ping.return_value = True # ping simulated
        helper.return_value.test_tcp.return_value = 0 # helper tcp ok
        socket.return_value.recv.side_effect = [
            codecs.decode('5050827d08000000d0075fb2cf450100', 'hex'), # tcp CMD_ACK_OK
            codecs.decode('5050827d10000000dc053b59d0983500f3030000f0030000', 'hex'), # tcp PREPARE_DATA 1011
            codecs.decode('5050827df8030000dd056855000035004ab153533231000003f2f10408050709ced000001bf36901000000831f256cf23e00740f4c008900f2f879005500fe0fe3005bf2d30a60005c00a00f32f26600580a2700ad00e3fd98007500800f000082f21a0f68008300300e5bf28d00570930004b00dafd4c009a00dd090900a8f2270f8600ad008a0b1ff2b000480f4400730040fc5400b800430f4400c6f2370ab100ca00f30ecbf2cb002f0f4a001300c7fdaa00e400b50c4300e6f2b706bf00ea00f90668f2f2002e0dad003000b7f7cf00f600350cbe0008f31f0dd0000c017101cbf20f019c01', 'hex'), # DATA (tcp 1016, actual 112 +104
            codecs.decode('5e00d4012dfdda001301a408e00019f3400c12002201fc0c4ff2570193096d0092018dfc3c7a62107e85688f818ff39a358ef99acb0fee06d47da2e2116a7c77f102a57bd1890a6a598b5ee2db0a0f64a384b28da105f29ca7eff9a137194560847d1565aa827ffc69705ffa8189f19f1f9ca10abbf2160f791a6e0dd8af0f723e062b6e84000a997780c100f6684b8016188780d7f44d0a', 'hex'), # raw 128 + 24
            codecs.decode('5083790fd0fa1a089ef44b807572db9b0900d9795083397a8780ca0161091489ae7b7c134278a6004c00b68bcf80e9f98982509a0e01dbf02e6a441a21138a70ddeaf1f9b16a8f1025f2ceef74f369094b70b2fb3a176bb339f9860f6459f304bb679757b3fca891ba733c4c6444c72032f303131c9705004b3079bc0600a03a89c405fdc03205004b456254c6006fb276c20a00a94343c2fc30779505001b4f862804f27d51faff31c2cd007fa50141c12f1800085a9431c181c4fe83c10674c33275300600245c89fcc0ad07005b5c6b88040503a96267c1830700e9695d30c1c2510a0031ae57', 'hex'), # raw 128 +104
            codecs.decode('5fa47a04007c7574510f039e80f0fd3bfefe9d55c3fa01c7841746ff06fa1ff2ee8ea07e787e0689c133c1c3c0c2ffc004c1fcae07005990578c040d03dc9350c0c4376a3a8623f2f29ea2c17c67b0928330726b6a83ff08c582afa8c5c3c3c1c3fec300895f0efdfd2809000bae21be5afd0c001cb68c59c20dc3fefda205004fb8150cfbc1030089bbffc30ef245bc467bc07404c288fd', 'hex'),  # raw 128 +24
            codecs.decode('0155bd46786445c3c130c0040091c52938c320f305c8a4c1ff7b05c08a63c3c2c1c2c3c13ac1c132c1ffc2c0c0c205c3c336050084c9306ec100b13f352c0700cacdf56b72f611f61a2d1605d5ef41a4fec0f818004c17c63e0dfef9c0fdfffe3b3649a0fac00c004ada856a6464c20b006cf83145c1c032c23d04109804d57617e28f07a0fe3bff3bfbfe0afc2ac0fdc138c01095f91bc543281101cbb0c19758fe9282c3c26270737997c1c0c2c0c204c70be27f0f2084c5fc070913ad1731c2c1c37b0125130c1ba958c049ff4e9bc6529262c1c290c2076ac2ed11e718a9554b068bc730b196', 'hex'),  # raw 128 +104
            codecs.decode('c2c1c2c1077dfc830210074929c1c910c5af81c0c1ffc2fe', 'hex'),  # raw 24?
            codecs.decode('5050827d0b000000dd054ba201003500a05701', 'hex'),  # raw 43-24 (104)

            codecs.decode('5050827d08000000d007fcf701003200', 'hex'),  # tcp CMD_ACK_OK
            codecs.decode('5050827d08000000d00745b2cf451b00', 'hex'),  # tcp random CMD_ACK_OK TODO: generate proper sequenced response
        ]
        #begin
        zk = ZK('192.168.1.201')#, verbose=True)
        conn = zk.connect()
        socket.return_value.send.assert_called_with(codecs.decode('5050827d08000000e80317fc00000000', 'hex'))
        template = conn.get_user_template(14, 1)
        self.assertEqual(template.size, 1010, "incorrect size %s" % template.size)
        self.assertEqual(template.mark, b"4ab1535332310000...81c0c1ffc2fea057", "incorrect mark %s" % template.mark)
        self.assertEqual(template.uid, 14, "incorrect uid %s" % template.uid)
        conn.disconnect()

    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def test_tcp_live_connect(self, helper, socket):
        """ check live_capture 12 bytes"""
        helper.return_value.test_ping.return_value = True # ping simulated
        helper.return_value.test_tcp.return_value = 0 # helper tcp ok
        socket.return_value.recv.side_effect = [
            codecs.decode('5050827d08000000d0075fb2cf450100', 'hex'), # tcp CMD_ACK_OK
            codecs.decode('5050827d64000000d007a3159663130000000000000000000000000000000000070000000000000006000000000000005d020000000000000f0c0000000000000100000000000000b80b000010270000a0860100b20b00000927000043840100000000000000', 'hex'), #sizes
            codecs.decode('5050827d04020000dd05942c96631500f801000001000e0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003830380000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003832310000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003833350000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003833310000000000000000000000000000000000000000000500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003833320000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003836000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000383432000000000000000000000000000000000000000000','hex'), #DATA directly(not ok)
            codecs.decode('5050827d08000000d00745b2cf451b00', 'hex'), # tcp random CMD_ACK_OK TODO: generate proper sequenced response
            codecs.decode('5050827d08000000d00745b2cf451b00', 'hex'),  # tcp random CMD_ACK_OK TODO: generate proper sequenced response
            codecs.decode('5050827d10000000dc053b59d0983500f401ae4301000000f19449000000120c07130906', 'hex'), # tcp PREPARE_DATA 1011
            codecs.decode('5050827df8030000f401ae4301000000f19449000000120c07130906', 'hex'), # reg_event!
            codecs.decode('5050827d08000000d007fcf701003200', 'hex'),  # tcp CMD_ACK_OK
            codecs.decode('5050827d08000000d00745b2cf451b00', 'hex'),  # tcp random CMD_ACK_OK TODO: generate proper sequenced response
        ]
        #begin
        zk = ZK('192.168.1.201')#, verbose=True)
        conn = zk.connect()
        socket.return_value.send.assert_called_with(codecs.decode('5050827d08000000e80317fc00000000', 'hex'))
        for att in conn.live_capture():
            #print att
            conn.end_live_capture = True
            self.assertEqual(att.user_id, "4822257", "incorrect user_id %s" % att.user_id)
        conn.disconnect()

    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def test_tcp_live_connect_small(self, helper, socket):
        """ check live_capture 32 bytes"""
        helper.return_value.test_ping.return_value = True # ping simulated
        helper.return_value.test_tcp.return_value = 0 # helper tcp ok
        socket.return_value.recv.side_effect = [
            codecs.decode('5050827d08000000d0075fb2cf450100', 'hex'), # tcp CMD_ACK_OK
            codecs.decode('5050827d64000000d007a3159663130000000000000000000000000000000000070000000000000006000000000000005d020000000000000f0c0000000000000100000000000000b80b000010270000a0860100b20b00000927000043840100000000000000', 'hex'), #sizes
            codecs.decode('5050827d04020000dd05942c96631500f801000001000e0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003830380000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003832310000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003833350000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003833310000000000000000000000000000000000000000000500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003833320000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003836000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000383432000000000000000000000000000000000000000000','hex'), #DATA directly(not ok)
            codecs.decode('5050827d08000000d00745b2cf451b00', 'hex'), # tcp random CMD_ACK_OK TODO: generate proper sequenced response
            codecs.decode('5050827d08000000d00745b2cf451b00', 'hex'),  # tcp random CMD_ACK_OK TODO: generate proper sequenced response
            codecs.decode('5050827d10000000dc053b59d0983500f401ae4301000000f19449000000120c07130906', 'hex'), # tcp PREPARE_DATA 1011
            codecs.decode('5050827df8030000f401ae43010000003131343030363400000000000000000000000000000000000f00120b1d0c3703', 'hex'), # reg_event!
            codecs.decode('5050827d08000000d007fcf701003200', 'hex'),  # tcp CMD_ACK_OK
            codecs.decode('5050827d08000000d00745b2cf451b00', 'hex'),  # tcp random CMD_ACK_OK TODO: generate proper sequenced response
        ]
        #begin
        zk = ZK('192.168.1.201')#, verbose=True)
        conn = zk.connect()
        socket.return_value.send.assert_called_with(codecs.decode('5050827d08000000e80317fc00000000', 'hex'))
        for att in conn.live_capture():
            #print att
            conn.end_live_capture = True
            self.assertEqual(att.user_id, "1140064", "incorrect user_id %s" % att.user_id)
        conn.disconnect()

if __name__ == '__main__':
    unittest.main()
