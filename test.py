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
        zk = ZK('192.168.1.201')
        helper.assert_called_with('192.168.1.201', 4370) # called correctly
        helper.return_value.test_ping.return_value = False #no ping simulated
        self.assertRaisesRegexp(ZKNetworkError, "can't reach device", zk.connect)

    @patch('zk.base.ZK_helper')
    def test_correct_ping(self,helper):
        """ what if ping is ok """
        helper.return_value.test_ping.return_value = True # ping simulated
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
        #socket.return_value.connect_ex.return_value = 0 # socket tcp ok
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
        zk = ZK('192.168.1.201', force_udp=True) # already tested
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
        zk = ZK('192.168.1.201', verbose=True) # already tested
        conn = zk.connect()
        conn.disconnect()

    @patch('zk.base.socket')
    @patch('zk.base.ZK_helper')
    def test_tcp_(self, helper, socket):
        """ Basic connection test """
        helper.return_value.test_ping.return_value = True # ping simulated
        helper.return_value.test_tcp.return_value = 0 # helper tcp ok
        socket.return_value.recv.return_value = codecs.decode('5050827d08000000d007fffc2ffb0000','hex') # tcp CMD_ACK_OK
        #begin
        zk = ZK('192.168.1.201') # already tested
        conn = zk.connect()
        conn.disconnect()



if __name__ == '__main__':
    unittest.main()