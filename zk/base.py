# -*- coding: utf-8 -*-
from datetime import datetime
from socket import AF_INET, SOCK_DGRAM, socket
from struct import pack, unpack

from zk import const
from zk.attendance import Attendance
from zk.exception import ZKErrorResponse, ZKNetworkError
from zk.user import User


class ZK(object):

    is_connect = False

    __data_recv = None
    __sesion_id = 0
    __reply_id = 0

    def __init__(self, ip, port=4370, timeout=60):
        self.__address = (ip, port)
        self.__sock = socket(AF_INET, SOCK_DGRAM)
        self.__sock.settimeout(timeout)

    def __create_header(self, command, command_string, checksum, session_id, reply_id):
        '''
        Puts a the parts that make up a packet together and packs them into a byte string
        '''
        buf = pack('HHHH', command, checksum, session_id, reply_id) + command_string
        buf = unpack('8B' + '%sB' % len(command_string), buf)
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

    def __send_command(self, command, command_string, checksum, session_id, reply_id, response_size):
        '''
        send command to the terminal
        '''
        buf = self.__create_header(command, command_string, checksum, session_id, reply_id)
        try:
            self.__sock.sendto(buf, self.__address)
            self.__data_recv = self.__sock.recv(response_size)
        except Exception, e:
            raise ZKNetworkError(str(e))

        self.__response = unpack('HHHH', self.__data_recv[:8])[0]
        self.__reply_id = unpack('HHHH', self.__data_recv[:8])[3]

        if self.__response in [const.CMD_ACK_OK, const.CMD_PREPARE_DATA]:
            return {
                'status': True,
                'code': self.__response
            }
        else:
            return {
                'status': False,
                'code': self.__response
            }

    def __get_data_size(self):
        """Checks a returned packet to see if it returned CMD_PREPARE_DATA,
        indicating that data packets are to be sent

        Returns the amount of bytes that are going to be sent"""
        response = self.__response
        if response == const.CMD_PREPARE_DATA:
            size = unpack('I', self.__data_recv[8:12])[0]
            return size
        else:
            return 0

    def __reverse_hex(self, hex):
        data = ''
        for i in reversed(xrange(len(hex) / 2)):
            data += hex[i * 2:(i * 2) + 2]
        return data

    def __decode_time(self, t):
        """Decode a timestamp retrieved from the timeclock

        copied from zkemsdk.c - DecodeTime"""
        t = t.encode('hex')
        t = int(self.__reverse_hex(t), 16)

        second = t % 60
        t = t / 60

        minute = t % 60
        t = t / 60

        hour = t % 24
        t = t / 24

        day = t % 31 + 1
        t = t / 31

        month = t % 12 + 1
        t = t / 12

        year = t + 2000

        d = datetime(year, month, day, hour, minute, second)

        return d

    def connect(self):
        '''
        connect to the device
        '''

        command = const.CMD_CONNECT
        command_string = ''
        checksum = 0
        session_id = 0
        reply_id = const.USHRT_MAX - 1
        response_size = 8

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            self.is_connect = True
            # set the session id
            self.__sesion_id = unpack('HHHH', self.__data_recv[:8])[2]
            return self
        else:
            raise ZKErrorResponse("Invalid response")

    def disconnect(self):
        '''
        diconnect from the connected device
        '''

        command = const.CMD_EXIT
        command_string = ''
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 8

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("Invalid response")

    def disable_device(self):
        '''
        disable (lock) device, ensure no activity when process run
        '''

        command = const.CMD_DISABLEDEVICE
        command_string = ''
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 8

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("Invalid response")

    def enable_device(self):
        '''
        re-enable the connected device
        '''

        command = const.CMD_ENABLEDEVICE
        command_string = ''
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 8

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("Invalid response")

    def get_firmware_version(self):
        '''
        return the firmware version
        '''

        command = const.CMD_GET_VERSION
        command_string = ''
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            firmware_version = self.__data_recv[8:].split('\x00')[0]
            return firmware_version
        else:
            raise ZKErrorResponse("Invalid response")

    def get_serialnumber(self):
        '''
        return the serial number
        '''
        command = const.CMD_OPTIONS_RRQ
        command_string = '~SerialNumber'
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            serialnumber = self.__data_recv[8:].split('=')[-1].split('\x00')[0]
            return serialnumber
        else:
            raise ZKErrorResponse("Invalid response")

    def restart(self):
        '''
        restart the device
        '''

        command = const.CMD_RESTART
        command_string = ''
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 8

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("Invalid response")

    def poweroff(self):
        '''
        shutdown the device
        '''

        command = const.CMD_POWEROFF
        command_string = ''
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 8

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("Invalid response")

    def test_voice(self):
        '''
        play test voice
        '''

        command = const.CMD_TESTVOICE
        command_string = ''
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 8

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("Invalid response")

    def set_user(self, uid, name, privilege, password='', group_id='', user_id=''):
        '''
        create or update user by uid
        '''

        command = const.CMD_USER_WRQ

        uid = chr(uid % 256) + chr(uid >> 8)
        if privilege not in [const.USER_DEFAULT, const.USER_ADMIN]:
            privilege = const.USER_DEFAULT
        privilege = chr(privilege)

        command_string = pack('2sc8s28sc7sx24s', uid, privilege, password, name, chr(0), group_id, user_id)
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("Invalid response")

    def delete_user(self, uid):
        '''
        delete specific user by uid
        '''
        command = const.CMD_DELETE_USER

        uid = chr(uid % 256) + chr(uid >> 8)

        command_string = pack('2s', uid)
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("Invalid response")

    def get_users(self):
        '''
        return all user
        '''

        command = const.CMD_USERTEMP_RRQ
        command_string = chr(const.FCT_USER)
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        users = []
        if cmd_response.get('status'):
            if cmd_response.get('code') == const.CMD_PREPARE_DATA:
                bytes = self.__get_data_size()
                userdata = []
                while bytes > 0:
                    data_recv = self.__sock.recv(1032)
                    userdata.append(data_recv)
                    bytes -= 1024

                data_recv = self.__sock.recv(8)
                response = unpack('HHHH', data_recv[:8])[0]
                if response == const.CMD_ACK_OK:
                    if userdata:
                        # The first 4 bytes don't seem to be related to the user
                        for x in xrange(len(userdata)):
                            if x > 0:
                                userdata[x] = userdata[x][8:]

                        userdata = ''.join(userdata)
                        userdata = userdata[12:]
                        while len(userdata) >= 72:
                            uid, privilege, password, name, sparator, group_id, user_id = unpack('2sc8s28sc7sx24s', userdata.ljust(72)[:72])
                            u1 = int(uid[0].encode("hex"), 16)
                            u2 = int(uid[1].encode("hex"), 16)

                            uid = u1 + (u2 * 256)
                            privilege = int(privilege.encode("hex"), 16)
                            password = unicode(password.split('\x00')[0], errors='ignore')
                            name = unicode(name.split('\x00')[0], errors='ignore')
                            group_id = unicode(group_id.split('\x00')[0], errors='ignore')
                            user_id = unicode(user_id.split('\x00')[0], errors='ignore')

                            user = User(uid, name, privilege, password, group_id, user_id)
                            users.append(user)

                            userdata = userdata[72:]
                else:
                    raise ZKErrorResponse("Invalid response")

        return users

    def cancel_capture(self):
        '''
        cancel capturing finger
        '''

        command = const.CMD_CANCELCAPTURE
        cmd_response = self.__send_command(command=command)
        print cmd_response

    def verify_user(self):
        '''
        verify finger
        '''

        command = const.CMD_STARTVERIFY
        # uid = chr(uid % 256) + chr(uid >> 8)
        cmd_response = self.__send_command(command=command)
        print cmd_response

    def enroll_user(self, uid=''):
        '''
        start enroll user
        '''

        command = const.CMD_STARTENROLL
        command_string = pack('2s', uid)
        
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 8
        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        print cmd_response
        
    def clear_data(self):
        '''
        clear all data (include: user, attendance report, finger database )
        '''
        command = const.CMD_CLEAR_DATA
        command_string = ''
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("Invalid response")

    def get_attendance(self):
        '''
        return all attendance record
        '''
        command = const.CMD_ATTLOG_RRQ
        command_string = ''
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        attendances = []
        if cmd_response.get('status'):
            if cmd_response.get('code') == const.CMD_PREPARE_DATA:
                bytes = self.__get_data_size()
                attendance_data = []
                while bytes > 0:
                    data_recv = self.__sock.recv(1032)
                    attendance_data.append(data_recv)
                    bytes -= 1024

                data_recv = self.__sock.recv(8)
                response = unpack('HHHH', data_recv[:8])[0]
                if response == const.CMD_ACK_OK:
                    if attendance_data:
                        # The first 4 bytes don't seem to be related to the user
                        for x in xrange(len(attendance_data)):
                            if x > 0:
                                attendance_data[x] = attendance_data[x][8:]

                        attendance_data = ''.join(attendance_data)
                        attendance_data = attendance_data[14:]
                        while len(attendance_data) >= 38:
                            user_id, sparator, timestamp, status, space = unpack('24sc4sc10s', attendance_data.ljust(40)[:40])

                            user_id = user_id.split('\x00')[0]
                            timestamp = self.__decode_time(timestamp)
                            status = int(status.encode("hex"), 16)

                            attendance = Attendance(user_id, timestamp, status)
                            attendances.append(attendance)

                            attendance_data = attendance_data[40:]
                else:
                    raise ZKErrorResponse("Invalid response")

        return attendances

    def clear_attendance(self):
        '''
        clear all attendance record
        '''
        command = const.CMD_CLEAR_ATTLOG
        command_string = ''
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("Invalid response")
