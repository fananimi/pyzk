# -*- coding: utf-8 -*-
from struct import pack, unpack
from socket import socket, AF_INET, SOCK_DGRAM

from zk import const

class ZK(object):

    __data_recv = None

    def __init__(self, ip, port=4370, timeout=5):
        self.__address = (ip, port)
        self.__sock = socket(AF_INET, SOCK_DGRAM)
        self.__sock.settimeout(timeout)

    def __create_header(self, command, checksum=0, session_id=0, reply_id=65534,  command_string=''):
        '''
        Puts a the parts that make up a packet together and packs them into a byte string
        '''
        buf = pack('HHHH', command, checksum, session_id, reply_id) + command_string        
        buf = unpack('8B'+'%sB' % len(command_string), buf)
        checksum = unpack('H', self.__create_checksum(buf))[0]
        reply_id += 1
        if reply_id >= const.USHRT_MAX:
            reply_id -= const.USHRT_MAX

        buf = pack('HHHH', command, checksum, session_id, reply_id)
        return buf + command_string

    def __create_checksum(self, p):
        '''
        Calculates the checksum of the packet to be sent to the time clock
        Copied from zkemsdk.c
        '''
        l = len(p)
        checksum = 0
        while l > 1:
            checksum += unpack('H', pack('BB', p[0], p[1]))[0]
            p = p[2:]
            if checksum > const.USHRT_MAX:
                checksum -= const.USHRT_MAX
            l -= 2
        if l:
            checksum = checksum + p[-1]
            
        while checksum > const.USHRT_MAX:
            checksum -= const.USHRT_MAX
        
        checksum = ~checksum
        
        while checksum < 0:
            checksum += const.USHRT_MAX

        return pack('H', checksum)

    def __send_command(self, command, checksum=0, command_string='', response_size=8):
        try:
            buf = self.__create_header(command, checksum, self.__sesion_id, self.__reply_id,  command_string)
            self.__sending_packet(buf)
            self.__receive_packet(response_size)

            if self.__response == const.CMD_ACK_OK:
                return {
                    'status': True,
                    'code': self.__response,
                    'message': 'success',
                    'data': self.__data_recv
                }
            else:
                return {
                    'status': False,
                    'code': self.__response,
                    'message': 'failed',
                    'data': self.__data_recv
                }
        except Exception, e:
            return {
                'status': False,
                'code': const.CMD_ACK_ERROR,
                'message': str(e),
                'data': ''
            }

    def __sending_packet(self, buf):
        self.__sock.sendto(buf, self.__address)

    def __receive_packet(self, buf_size):
        self.__data_recv = self.__sock.recv(buf_size)

    @property
    def __response(self):
        '''
        Checks a returned packet to see if it returned `CMD_ACK_OK` indicating success
        '''
        return unpack('HHHH', self.__data_recv[:8])[0]

    @property
    def __sesion_id(self):
        if not self.__data_recv:
            return 0
        return unpack('HHHH', self.__data_recv[:8])[2]

    @property
    def __reply_id(self):
        if not self.__data_recv:
            return const.USHRT_MAX - 1
        return unpack('HHHH', self.__data_recv[:8])[3]

    def connect(self):
        '''
        connect to device
        '''

        command = const.CMD_CONNECT
        cmd_response = self.__send_command(command)
        cmd_response['data'] = ''
        if cmd_response.get('status'):
            cmd_response['message'] = 'connected'
            return cmd_response
        else:
            return cmd_response

    def disconnect(self):
        '''
        diconnect from connected device
        '''

        command = const.CMD_EXIT
        cmd_response = self.__send_command(command)
        cmd_response['data'] = ''
        if cmd_response.get('status'):
            cmd_response['message'] = 'disconnected'
            return cmd_response
        else:
            return cmd_response

    def get_firmware_version(self):
        command = const.CMD_GET_VERSION
        cmd_response = self.__send_command(command, response_size=1024)
        if cmd_response.get('status'):
            cmd_response['data'] = cmd_response.get('data')[8:].strip('\x00|\x01\x10x')
            return cmd_response
        else:
            cmd_response['data'] = ''
            return cmd_response

    def restart(self):
        '''
        shutdown device
        '''

        command = const.CMD_RESTART
        cmd_response = self.__send_command(command)
        cmd_response['data'] = ''
        if cmd_response.get('status'):
            cmd_response['message'] = 'device restarted'
            return cmd_response
        else:
            return cmd_response

    def power_off(self):
        '''
        shutdown device
        '''

        command = const.CMD_POWEROFF
        cmd_response = self.__send_command(command)
        cmd_response['data'] = ''
        if cmd_response.get('status'):
            cmd_response['message'] = 'device turning off'
            return cmd_response
        else:
            return cmd_response

    def disable_device(self):
        command = const.CMD_DISABLEDEVICE
        cmd_response = self.__send_command(command)
        cmd_response['data'] = ''
        if cmd_response.get('status'):
            cmd_response['message'] = 'device disabled'
            return cmd_response
        else:
            return cmd_response

    def enable_device(self):
        command = const.CMD_ENABLEDEVICE
        cmd_response = self.__send_command(command)
        cmd_response['data'] = ''
        if cmd_response.get('status'):
            cmd_response['message'] = 'device enabled'
            return cmd_response
        else:
            return cmd_response

    def test_voice(self):
        command = const.CMD_TESTVOICE
        cmd_response = self.__send_command(command)
        cmd_response['data'] = ''
        if cmd_response.get('status'):
            cmd_response['message'] = 'voice detected'
            return cmd_response
        else:
            return cmd_response

    def set_user(self, uid, name, password='', privilege=0, grup_id='', user_id=''):
        command = const.CMD_USER_WRQ

        uid = chr(uid % 256) + chr(uid >> 8)

        if privilege not in [const.USER_DEFAULT, const.USER_ADMIN]:
            privilege = const.USER_DEFAULT
        privilege = chr(privilege)

        command_string = pack('2sc6s30sc8s24s', uid, privilege, password, name, chr(0), grup_id, user_id)
        cmd_response = self.__send_command(command=command, command_string=command_string, response_size=1024)
        cmd_response['data'] = ''
        if cmd_response.get('status'):
            cmd_response['message'] = 'new user created'
            return cmd_response
        else:
            return cmd_response

    # def __get_size_user(self):
    #     """Checks a returned packet to see if it returned CMD_PREPARE_DATA,
    #     indicating that data packets are to be sent

    #     Returns the amount of bytes that are going to be sent"""
    #     response = self.__response
    #     if response == const.CMD_PREPARE_DATA:
    #         size = unpack('I', self.__data_recv[8:12])[0]
    #         return size
    #     else:
    #         return 0

    # def get_users(self):
    #     command = const.CMD_USERTEMP_RRQ
    #     command_string = chr(5)

    #     try:
    #         buf = self.__create_header(command=command, session_id=self.__sesion_id, reply_id=self.__reply_id, command_string=command_string)
    #         self.__sending_packet(buf)
    #         self.__receive_packet(1024)

    #         bytes = self.__get_size_user()
    #         userdata = []

    #         if bytes:
    #             while bytes > 0:
    #                 data_recv, addr = self.__sock.recvfrom(1032)
    #                 userdata.append(data_recv)
    #                 bytes -= 1024

    #             self.__receive_packet(8)

    #         users = {}
    #         if len(userdata) > 0:
    #             # The first 4 bytes don't seem to be related to the user
    #             for x in xrange(len(userdata)):
    #                 if x > 0:
    #                     userdata[x] = userdata[x][8:]

    #             userdata = ''.join(userdata)
    #             userdata = userdata[11:]

    #             while len(userdata) > 72:
    #                 uid, role, password, name, userid = unpack( '2s2s8s28sx31s', userdata.ljust(72)[:72])

    #                 uid = int( uid.encode("hex"), 16)
    #                 # Clean up some messy characters from the user name
    #                 password = password.split('\x00', 1)[0]
    #                 password = unicode(password.strip('\x00|\x01\x10x'), errors='ignore')

    #                 userid = unicode(userid.strip('\x00|\x01\x10x'), errors='ignore')

    #                 name = name.split('\x00', 1)[0]

    #                 if not name:
    #                     name = uid

    #                 users[uid] = (userid, name, int( role.encode("hex"), 16 ), password)

    #                 userdata = userdata[72:]

    #         return users
    #     except Exception, e:
    #         return (False, e)

