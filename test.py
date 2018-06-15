import sys
import os
import unittest
import codecs
from mock import patch, Mock, MagicMock
mock_socket = MagicMock(name='zk.socket')
sys.modules['zk.socket'] = mock_socket
from zk import ZK, const
from zk.base import ZK_helper
from zk.user import User
from zk.finger import Finger
from zk.attendance import Attendance
from zk.exception import ZKErrorResponse, ZKNetworkError
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
    
    @patch('zk.base.ZK_helper')
    def test_no_ping(self,helper):
        """ what if ping doesn't response """
        helper.return_value.test_ping.return_value = False #no ping simulated
        #begin
        zk = ZK('192.168.1.201')
        helper.assert_called_with('192.168.1.201', 4370) # called correctly
        self.assertRaisesRegexp(ZKNetworkError, "can't reach device", zk.connect)

    @patch('zk.base.ZK_helper')
    def test_correct_ping(self,helper):
        """ what if ping is ok """
        helper.return_value.test_ping.return_value = True # ping simulated
        #begin
        zk = ZK('192.168.1.201')
        helper.assert_called_with('192.168.1.201', 4370) # called correctly
        self.assertRaisesRegexp(ZKNetworkError, "unpack requires", zk.connect) # no data...?

    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def test_tcp_invalid(self, helper, socket):
        """ Basic connection test """
        helper.return_value.test_ping.return_value = True # ping simulated
        helper.return_value.test_tcp.return_value = 0 # helper tcp ok
        socket.return_value.recv.return_value = 'Invalid tcp data'
        #begin
        zk = ZK('192.168.1.201')
        helper.assert_called_with('192.168.1.201', 4370) # called correctly
        self.assertRaisesRegexp(ZKNetworkError, "TCP packet invalid", zk.connect)

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
        zk = ZK('192.168.1.201')
        conn = zk.connect()
        socket.return_value.sendto.assert_called_with(codecs.decode('e80317fc00000000', 'hex'), ('192.168.1.201', 4370))
        conn.disconnect()
        socket.return_value.sendto.assert_called_with(codecs.decode('e903e6002ffb0100', 'hex'), ('192.168.1.201', 4370))

    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def test_tcp_unauth(self, helper, socket):
        """ Basic auth test """
        helper.return_value.test_ping.return_value = True # ping simulated
        helper.return_value.test_tcp.return_value = 0 # helper tcp ok
        socket.return_value.recv.side_effect = [
            codecs.decode('5050827d08000000d5075bb2cf450000', 'hex'), # tcp CMD_UNAUTH
            codecs.decode('5050827d08000000d5075ab2cf450100', 'hex') # tcp CMD_UNAUTH
        ]
        #begin
        zk = ZK('192.168.1.201', password=12)
        self.assertRaisesRegexp(ZKErrorResponse, "Unauthenticated", zk.connect)
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
    def test_tcp_get_users_small(self, helper, socket):
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
        self.assertIsInstance(usu.user_id, (str, unicode), "user_id should be str() or unicode() %s" % type(usu.user_id))
        self.assertEqual(usu.uid, 4, "incorrect uid %s" % usu.uid)
        self.assertEqual(usu.user_id, "831", "incorrect user_id %s" % usu.user_id)
        self.assertEqual(usu.name, "NN-831", "incorrect uid %s" % usu.name) # generated
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
        self.assertIsInstance(usu.user_id, (str, unicode), "user_id should be str() or unicode() %s" % type(usu.user_id))
        self.assertEqual(usu.uid, 4, "incorrect uid %s" % usu.uid)
        self.assertEqual(usu.user_id, "831", "incorrect user_id %s" % usu.user_id)
        self.assertEqual(usu.name, "NN-831", "incorrect uid %s" % usu.name) # generated
        conn.disconnect()

if __name__ == '__main__':
    unittest.main()