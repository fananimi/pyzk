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

    def __create_header(self, command, chksum=0, session_id=0, reply_id=65534,  command_string=''):
        '''
        Puts a the parts that make up a packet together and packs them into a byte string
        '''
        buf = pack('HHHH', command, chksum, session_id, reply_id) + command_string        
        buf = unpack('8B'+'%sB' % len(command_string), buf)
        chksum = unpack('H', self.__create_checksum(buf))[0]
        reply_id += 1
        if reply_id >= const.USHRT_MAX:
            reply_id -= const.USHRT_MAX

        buf = pack('HHHH', command, chksum, session_id, reply_id)
        return buf + command_string

    def __create_checksum(self, p):
        '''
        Calculates the chksum of the packet to be sent to the time clock
        Copied from zkemsdk.c
        '''
        l = len(p)
        chksum = 0
        while l > 1:
            chksum += unpack('H', pack('BB', p[0], p[1]))[0]
            p = p[2:]
            if chksum > const.USHRT_MAX:
                chksum -= const.USHRT_MAX
            l -= 2
        if l:
            chksum = chksum + p[-1]
            
        while chksum > const.USHRT_MAX:
            chksum -= const.USHRT_MAX
        
        chksum = ~chksum
        
        while chksum < 0:
            chksum += const.USHRT_MAX

        return pack('H', chksum)

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
        return unpack('HHHH', self.__data_recv[:8])[2]

    @property
    def __reply_id(self):
        return unpack('HHHH', self.__data_recv[:8])[3]

    def connect(self):
        '''
        connect to device
        '''

        command = const.CMD_CONNECT
        try:
            buf = self.__create_header(command=command)
            self.__sending_packet(buf)
            self.__receive_packet(8)

            if self.__response == const.CMD_ACK_OK:
                return (True, self.__response)
            else:
                return (False, self.__response)
        except Exception, e:
            return (False, e)

    def disconnect(self):
        '''
        diconnect from connected device
        '''

        command = const.CMD_EXIT
        try:
            buf = self.__create_header(command=command, session_id=self.__sesion_id, reply_id=self.__reply_id)
            self.__sending_packet(buf)
            self.__receive_packet(8)
            if self.__response == const.CMD_ACK_OK:
                return (True, self.__response)
            else:
                return (False, self.__response)
        except Exception, e:
            return (False, e)

    def get_firmware_version(self):
        command = const.CMD_GET_VERSION
        try:
            buf = self.__create_header(command=command, session_id=self.__sesion_id, reply_id=self.__reply_id)
            self.__sending_packet(buf)
            self.__receive_packet(1024)
            if self.__response == const.CMD_ACK_OK:
                version = self.__data_recv[8:]
                return version
            else:
                return (False, self.__response)
        except Exception, e:
            return (False, e)

    def restart(self):
        '''
        shutdown device
        '''

        command = const.CMD_RESTART
        try:
            buf = self.__create_header(command=command, session_id=self.__sesion_id, reply_id=self.__reply_id)
            self.__sending_packet(buf)
            self.__receive_packet(8)
            if self.__response == const.CMD_ACK_OK:
                return (True, self.__response)
            else:
                return (False, self.__response)
        except Exception, e:
            return (False, e)

    def power_off(self):
        '''
        shutdown device
        '''

        command = const.CMD_POWEROFF
        try:
            buf = self.__create_header(command=command, session_id=self.__sesion_id, reply_id=self.__reply_id)
            self.__sending_packet(buf)
            self.__receive_packet(8)
            if self.__response == const.CMD_ACK_OK:
                return (True, self.__response)
            else:
                return (False, self.__response)
        except Exception, e:
            return (False, e)

    def __get_size_user(self):
        """Checks a returned packet to see if it returned CMD_PREPARE_DATA,
        indicating that data packets are to be sent

        Returns the amount of bytes that are going to be sent"""
        response = self.__response
        if response == const.CMD_PREPARE_DATA:
            size = unpack('I', self.__data_recv[8:12])[0]
            return size
        else:
            return 0

    def get_users(self):
        command = const.CMD_USERTEMP_RRQ
        command_string = chr(5)

        try:
            buf = self.__create_header(command=command, session_id=self.__sesion_id, reply_id=self.__reply_id, command_string=command_string)
            self.__sending_packet(buf)
            self.__receive_packet(1024)

            bytes = self.__get_size_user()
            userdata = []

            if bytes:
                while bytes > 0:
                    data_recv, addr = self.__sock.recvfrom(1032)
                    userdata.append(data_recv)
                    bytes -= 1024

                self.__receive_packet(8)

            users = {}
            if len(userdata) > 0:
                # The first 4 bytes don't seem to be related to the user
                for x in xrange(len(userdata)):
                    if x > 0:
                        userdata[x] = userdata[x][8:]

                userdata = ''.join(userdata)
                userdata = userdata[11:]

                while len(userdata) > 72:
                    uid, role, password, name, userid = unpack( '2s2s8s28sx31s', userdata.ljust(72)[:72])

                    uid = int( uid.encode("hex"), 16)
                    # Clean up some messy characters from the user name
                    password = password.split('\x00', 1)[0]
                    password = unicode(password.strip('\x00|\x01\x10x'), errors='ignore')

                    userid = unicode(userid.strip('\x00|\x01\x10x'), errors='ignore')

                    name = name.split('\x00', 1)[0]

                    if not name:
                        name = uid

                    users[uid] = (userid, name, int( role.encode("hex"), 16 ), password)

                    userdata = userdata[72:]

            return users
        except Exception, e:
            return (False, e)

