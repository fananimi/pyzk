# -*- coding: utf-8 -*-
import sys
from datetime import datetime
from socket import AF_INET, SOCK_DGRAM, SOCK_STREAM, socket, timeout
from struct import pack, unpack
import codecs

from . import const
from .attendance import Attendance
from .exception import ZKErrorConnection, ZKErrorResponse, ZKNetworkError
from .user import User
from .finger import Finger


def safe_cast(val, to_type, default=None):
    #https://stackoverflow.com/questions/6330071/safe-casting-in-python
    try:
        return to_type(val)
    except (ValueError, TypeError):
        return default


def make_commkey(key, session_id, ticks=50):
    """
    take a password and session_id and scramble them to send to the machine.
    copied from commpro.c - MakeKey
    """
    key = int(key)
    session_id = int(session_id)
    k = 0
    for i in range(32):
        if (key & (1 << i)):
            k = (k << 1 | 1)
        else:
            k = k << 1
    k += session_id

    k = pack(b'I', k)
    k = unpack(b'BBBB', k)
    k = pack(
        b'BBBB',
        k[0] ^ ord('Z'),
        k[1] ^ ord('K'),
        k[2] ^ ord('S'),
        k[3] ^ ord('O'))
    k = unpack(b'HH', k)
    k = pack(b'HH', k[1], k[0])

    B = 0xff & ticks
    k = unpack(b'BBBB', k)
    k = pack(
        b'BBBB',
        k[0] ^ B,
        k[1] ^ B,
        B,
        k[3] ^ B)
    return k


class ZK_helper(object):
    """
    ZK helper class
    """

    def __init__(self, ip, port=4370):
        """
        Construct a new 'ZK_helper' object.
        """
        self.address = (ip, port)
        self.ip = ip
        self.port = port

    def test_ping(self):
        """
        Returns True if host responds to a ping request

        :return: bool
        """
        import subprocess, platform
        # Ping parameters as function of OS
        ping_str = "-n 1" if  platform.system().lower()=="windows" else "-c 1 -W 5"
        args = "ping " + " " + ping_str + " " + self.ip
        need_sh = False if  platform.system().lower()=="windows" else True
        # Ping
        return subprocess.call(args,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=need_sh) == 0

    def test_tcp(self):
        """
        test TCP connection
        """

        self.client = socket(AF_INET, SOCK_STREAM)
        self.client.settimeout(10)
        res = self.client.connect_ex(self.address)
        self.client.close()
        return res

    def test_udp(self):
        """
        test UDP connection
        """
        self.client = socket(AF_INET, SOCK_DGRAM)
        self.client.settimeout(10)


class ZK(object):
    """
    ZK main class
    """
    def __init__(self, ip, port=4370, timeout=60, password=0, force_udp=False, ommit_ping=False, verbose=False, encoding='UTF-8'):
        """
        Construct a new 'ZK' object.

        :param ip: machine's IP address
        :param port: machine's port
        :param timeout: timeout number
        :param password: passint
        :param force_udp: use UDP connection
        :param omit_ping: check ip using ping before connect
        :param verbose: showing log while run the commands
        :param encoding: user encoding
        """
        User.encoding = encoding
        self.__address = (ip, port)
        self.__sock = socket(AF_INET, SOCK_DGRAM)
        self.__sock.settimeout(timeout)
        self.__timeout = timeout
        self.__password = password # passint
        self.__session_id = 0
        self.__reply_id = const.USHRT_MAX - 1
        self.__data_recv = None
        self.__data = None

        self.is_connect = False
        self.is_enabled = True
        self.helper = ZK_helper(ip, port)
        self.force_udp = force_udp
        self.ommit_ping = ommit_ping
        self.verbose = verbose
        self.encoding = encoding
        self.tcp = not force_udp
        self.users = 0
        self.fingers = 0
        self.records = 0
        self.dummy = 0
        self.cards = 0
        self.fingers_cap = 0
        self.users_cap = 0
        self.rec_cap = 0
        self.faces = 0
        self.faces_cap = 0
        self.fingers_av = 0
        self.users_av = 0
        self.rec_av = 0
        self.next_uid = 1
        self.next_user_id='1'
        self.user_packet_size = 28 # default zk6
        self.end_live_capture = False

    def __nonzero__(self):
        """
        for boolean test
        """
        return self.is_connect

    def __create_socket(self):
        if self.tcp:
            self.__sock = socket(AF_INET, SOCK_STREAM)
            self.__sock.settimeout(self.__timeout)
            self.__sock.connect_ex(self.__address)
        else:
            self.__sock = socket(AF_INET, SOCK_DGRAM)
            self.__sock.settimeout(self.__timeout)

    def __create_tcp_top(self, packet):
        """
        witch the complete packet set top header
        """
        length = len(packet)
        top = pack('<HHI', const.MACHINE_PREPARE_DATA_1, const.MACHINE_PREPARE_DATA_2, length)
        return top + packet

    def __create_header(self, command, command_string, session_id, reply_id):
        """
        Puts a the parts that make up a packet together and packs them into a byte string
        """
        buf = pack('<4H', command, 0, session_id, reply_id) + command_string
        buf = unpack('8B' + '%sB' % len(command_string), buf)
        checksum = unpack('H', self.__create_checksum(buf))[0]
        reply_id += 1
        if reply_id >= const.USHRT_MAX:
            reply_id -= const.USHRT_MAX

        buf = pack('<4H', command, checksum, session_id, reply_id)
        return buf + command_string

    def __create_checksum(self, p):
        """
        Calculates the checksum of the packet to be sent to the time clock
        Copied from zkemsdk.c
        """
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

    def __test_tcp_top(self, packet):
        """
        return size!
        """
        if len(packet)<=8:
            return 0
        tcp_header = unpack('<HHI', packet[:8])
        if tcp_header[0] == const.MACHINE_PREPARE_DATA_1 and tcp_header[1] == const.MACHINE_PREPARE_DATA_2:
            return tcp_header[2]
        return 0

    def __send_command(self, command, command_string=b'', response_size=8):
        """
        send command to the terminal
        """
        if command not in [const.CMD_CONNECT, const.CMD_AUTH] and not self.is_connect:
            raise ZKErrorConnection("instance are not connected.")

        buf = self.__create_header(command, command_string, self.__session_id, self.__reply_id)
        try:
            if self.tcp:
                top = self.__create_tcp_top(buf)
                self.__sock.send(top)
                self.__tcp_data_recv = self.__sock.recv(response_size + 8)
                self.__tcp_length = self.__test_tcp_top(self.__tcp_data_recv)
                if self.__tcp_length == 0:
                    raise ZKNetworkError("TCP packet invalid")
                self.__header = unpack('<4H', self.__tcp_data_recv[8:16])
                self.__data_recv = self.__tcp_data_recv[8:]
            else:
                self.__sock.sendto(buf, self.__address)
                self.__data_recv = self.__sock.recv(response_size)
                self.__header = unpack('<4H', self.__data_recv[:8])
        except Exception as e:
            raise ZKNetworkError(str(e))

        self.__response = self.__header[0]
        self.__reply_id = self.__header[3]
        self.__data = self.__data_recv[8:]
        if self.__response in [const.CMD_ACK_OK, const.CMD_PREPARE_DATA, const.CMD_DATA]:
            return {
                'status': True,
                'code': self.__response
            }
        return {
            'status': False,
            'code': self.__response
        }

    def __ack_ok(self):
        """
        event ack ok
        """
        buf = self.__create_header(const.CMD_ACK_OK, b'', self.__session_id, const.USHRT_MAX - 1)
        try:
            if self.tcp:
                top = self.__create_tcp_top(buf)
                self.__sock.send(top)
            else:
                self.__sock.sendto(buf, self.__address)
        except Exception as e:
            raise ZKNetworkError(str(e))

    def __get_data_size(self):
        """
        Checks a returned packet to see if it returned CMD_PREPARE_DATA,
        indicating that data packets are to be sent

        Returns the amount of bytes that are going to be sent
        """
        response = self.__response
        if response == const.CMD_PREPARE_DATA:
            size = unpack('I', self.__data[:4])[0]
            return size
        else:
            return 0

    def __reverse_hex(self, hex):
        data = ''
        for i in reversed(range(len(hex) / 2)):
            data += hex[i * 2:(i * 2) + 2]
        return data

    def __decode_time(self, t):
        """
        Decode a timestamp retrieved from the timeclock

        copied from zkemsdk.c - DecodeTime
        """

        t = unpack("<I", t)[0]
        second = t % 60
        t = t // 60

        minute = t % 60
        t = t // 60

        hour = t % 24
        t = t // 24

        day = t % 31 + 1
        t = t // 31

        month = t % 12 + 1
        t = t // 12

        year = t + 2000

        d = datetime(year, month, day, hour, minute, second)

        return d

    def __decode_timehex(self, timehex):
        """
        timehex string of six bytes
        """
        year, month, day, hour, minute, second = unpack("6B", timehex)
        year += 2000
        d = datetime(year, month, day, hour, minute, second)
        return d

    def __encode_time(self, t):
        """
        Encode a timestamp so that it can be read on the timeclock
        """
        # formula taken from zkemsdk.c - EncodeTime
        # can also be found in the technical manual
        d = (
            ((t.year % 100) * 12 * 31 + ((t.month - 1) * 31) + t.day - 1) *
            (24 * 60 * 60) + (t.hour * 60 + t.minute) * 60 + t.second
        )
        return d

    def connect(self):
        """
        connect to the device

        :return: bool
        """
        self.end_live_capture = False
        if not self.ommit_ping and not self.helper.test_ping():
            raise ZKNetworkError("can't reach device (ping %s)" % self.__address[0])
        if not self.force_udp and self.helper.test_tcp() == 0:
            self.user_packet_size = 72 # default zk8
        self.__create_socket()
        self.__session_id = 0
        self.__reply_id = const.USHRT_MAX - 1
        cmd_response = self.__send_command(const.CMD_CONNECT)
        self.__session_id = self.__header[2]
        if cmd_response.get('code') == const.CMD_ACK_UNAUTH:
            if self.verbose: print ("try auth")
            command_string = make_commkey(self.__password, self.__session_id)
            cmd_response = self.__send_command(const.CMD_AUTH, command_string)
        if cmd_response.get('status'):
            self.is_connect = True
            return self
        else:
            if cmd_response["code"] == const.CMD_ACK_UNAUTH:
                raise ZKErrorResponse("Unauthenticated")
            if self.verbose: print ("connect err response {} ".format(cmd_response["code"]))
            raise ZKErrorResponse("Invalid response: Can't connect")

    def disconnect(self):
        """
        diconnect from the connected device

        :return: bool
        """
        cmd_response = self.__send_command(const.CMD_EXIT)
        if cmd_response.get('status'):
            self.is_connect = False
            if self.__sock:
                self.__sock.close()
            return True
        else:
            raise ZKErrorResponse("can't disconnect")

    def enable_device(self):
        """
        re-enable the connected device and allow user activity in device again

        :return: bool
        """
        cmd_response = self.__send_command(const.CMD_ENABLEDEVICE)
        if cmd_response.get('status'):
            self.is_enabled = True
            return True
        else:
            raise ZKErrorResponse("Can't enable device")

    def disable_device(self):
        """
        disable (lock) device, to ensure no user activity in device while some process run

        :return: bool
        """
        cmd_response = self.__send_command(const.CMD_DISABLEDEVICE)
        if cmd_response.get('status'):
            self.is_enabled = False
            return True
        else:
            raise ZKErrorResponse("Can't disable device")

    def get_firmware_version(self):
        """
        :return: the firmware version
        """
        cmd_response = self.__send_command(const.CMD_GET_VERSION,b'', 1024)
        if cmd_response.get('status'):
            firmware_version = self.__data.split(b'\x00')[0]
            return firmware_version.decode()
        else:
            raise ZKErrorResponse("Can't read frimware version")

    def get_serialnumber(self):
        """
        :return: the serial number
        """
        command = const.CMD_OPTIONS_RRQ
        command_string = b'~SerialNumber\x00'
        response_size = 1024
        cmd_response = self.__send_command(command, command_string, response_size)
        if cmd_response.get('status'):
            serialnumber = self.__data.split(b'=', 1)[-1].split(b'\x00')[0]
            serialnumber = serialnumber.replace(b'=', b'')
            return serialnumber.decode() # string?
        else:
            raise ZKErrorResponse("Can't read serial number")

    def get_platform(self):
        """
        :return: the platform name
        """
        command = const.CMD_OPTIONS_RRQ
        command_string = b'~Platform\x00'
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, response_size)
        if cmd_response.get('status'):
            platform = self.__data.split(b'=', 1)[-1].split(b'\x00')[0]
            platform = platform.replace(b'=', b'')
            return platform.decode()
        else:
            raise ZKErrorResponse("Can't read platform name")

    def get_mac(self):
        """
        :return: the machine's mac address
        """
        command = const.CMD_OPTIONS_RRQ
        command_string = b'MAC\x00'
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, response_size)
        if cmd_response.get('status'):
            mac = self.__data.split(b'=', 1)[-1].split(b'\x00')[0]
            return mac.decode()
        else:
            raise ZKErrorResponse("can't read mac address")

    def get_device_name(self):
        """
        return the device name

        :return: str
        """
        command = const.CMD_OPTIONS_RRQ
        command_string = b'~DeviceName\x00'
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, response_size)
        if cmd_response.get('status'):
            device = self.__data.split(b'=', 1)[-1].split(b'\x00')[0]
            return device.decode()
        else:
            return ""

    def get_face_version(self):
        """
        :return: the face version
        """
        command = const.CMD_OPTIONS_RRQ
        command_string = b'ZKFaceVersion\x00'
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, response_size)
        if cmd_response.get('status'):
            response = self.__data.split(b'=', 1)[-1].split(b'\x00')[0]
            return safe_cast(response, int, 0)  if response else 0
        else:
            return None

    def get_fp_version(self):
        """
        :return: the fingerprint version
        """
        command = const.CMD_OPTIONS_RRQ
        command_string = b'~ZKFPVersion\x00'
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, response_size)
        if cmd_response.get('status'):
            response = self.__data.split(b'=', 1)[-1].split(b'\x00')[0]
            response = response.replace(b'=', b'')
            return safe_cast(response, int, 0) if response else 0
        else:
            raise ZKErrorResponse("can't read fingerprint version")

    def _clear_error(self, command_string=b''):
        """
        clear ACK_error
        """
        cmd_response = self.__send_command(const.CMD_ACK_ERROR, command_string, 1024)
        cmd_response = self.__send_command(const.CMD_ACK_UNKNOWN, command_string, 1024)
        cmd_response = self.__send_command(const.CMD_ACK_UNKNOWN, command_string, 1024)
        cmd_response = self.__send_command(const.CMD_ACK_UNKNOWN, command_string, 1024)

    def get_extend_fmt(self):
        """
        determine extend fmt
        """
        command = const.CMD_OPTIONS_RRQ
        command_string = b'~ExtendFmt\x00'
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, response_size)
        if cmd_response.get('status'):
            fmt = (self.__data.split(b'=', 1)[-1].split(b'\x00')[0])
            return safe_cast(fmt, int, 0) if fmt else 0
        else:
            self._clear_error(command_string)
            return None

    def get_user_extend_fmt(self):
        """
        determine user extend fmt
        """
        command = const.CMD_OPTIONS_RRQ
        command_string = b'~UserExtFmt\x00'
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, response_size)
        if cmd_response.get('status'):
            fmt = (self.__data.split(b'=', 1)[-1].split(b'\x00')[0])
            return safe_cast(fmt, int, 0) if fmt else 0
        else:
            self._clear_error(command_string)
            return None

    def get_face_fun_on(self):
        """
        determine extend fmt
        """
        command = const.CMD_OPTIONS_RRQ
        command_string = b'FaceFunOn\x00'
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, response_size)
        if cmd_response.get('status'):
            response = (self.__data.split(b'=', 1)[-1].split(b'\x00')[0])
            return safe_cast(response, int ,0) if response else 0
        else:
            self._clear_error(command_string)
            return None

    def get_compat_old_firmware(self):
        """
        determine old firmware
        """
        command = const.CMD_OPTIONS_RRQ
        command_string = b'CompatOldFirmware\x00'
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, response_size)
        if cmd_response.get('status'):
            response = (self.__data.split(b'=', 1)[-1].split(b'\x00')[0])
            return safe_cast(response, int, 0) if response else 0
        else:
            self._clear_error(command_string)
            return None

    def get_network_params(self):
        """
        get network params
        """
        ip = self.__address[0]
        mask = b''
        gate = b''
        cmd_response = self.__send_command(const.CMD_OPTIONS_RRQ, b'IPAddress\x00', 1024)
        if cmd_response.get('status'):
            ip = (self.__data.split(b'=', 1)[-1].split(b'\x00')[0])
        cmd_response = self.__send_command(const.CMD_OPTIONS_RRQ, b'NetMask\x00', 1024)
        if cmd_response.get('status'):
            mask = (self.__data.split(b'=', 1)[-1].split(b'\x00')[0])
        cmd_response = self.__send_command(const.CMD_OPTIONS_RRQ, b'GATEIPAddress\x00', 1024)
        if cmd_response.get('status'):
            gate = (self.__data.split(b'=', 1)[-1].split(b'\x00')[0])
        return {'ip': ip.decode(), 'mask': mask.decode(), 'gateway': gate.decode()}

    def get_pin_width(self):
        """
        :return: the PIN width
        """
        command = const.CMD_GET_PINWIDTH
        command_string = b' P'
        response_size = 9
        cmd_response = self.__send_command(command, command_string, response_size)
        if cmd_response.get('status'):
            width = self.__data.split(b'\x00')[0]
            return bytearray(width)[0]
        else:
            raise ZKErrorResponse("can0t get pin width")

    def free_data(self):
        """
        clear buffer

        :return: bool
        """
        command = const.CMD_FREE_DATA
        cmd_response = self.__send_command(command)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("can't free data")

    def read_sizes(self):
        """
        read the memory ussage
        """
        command = const.CMD_GET_FREE_SIZES
        response_size = 1024
        cmd_response = self.__send_command(command,b'', response_size)
        if cmd_response.get('status'):
            if self.verbose: print(codecs.encode(self.__data,'hex'))
            size = len(self.__data)
            if len(self.__data) >= 80:
                fields = unpack('20i', self.__data[:80])
                self.users = fields[4]
                self.fingers = fields[6]
                self.records = fields[8]
                self.dummy = fields[10] #???
                self.cards = fields[12]
                self.fingers_cap = fields[14]
                self.users_cap = fields[15]
                self.rec_cap = fields[16]
                self.fingers_av = fields[17]
                self.users_av = fields[18]
                self.rec_av = fields[19]
                self.__data = self.__data[80:]
            if len(self.__data) >= 12: #face info
                fields = unpack('3i', self.__data[:12]) #dirty hack! we need more information
                self.faces = fields[0]
                self.faces_cap = fields[2]
            return True
        else:
            raise ZKErrorResponse("can't read sizes")

    def unlock(self, time=3):
        """
        unlock the door\n
        thanks to https://github.com/SoftwareHouseMerida/pyzk/

        :param time: define delay in seconds
        :return: bool
        """
        command = const.CMD_UNLOCK
        command_string = pack("I",int(time)*10)
        cmd_response = self.__send_command(command, command_string)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("Can't open door")
    def get_lock_state(self):
        '''
        :return: boolean
        thanks to https://github.com/icarome/pyzk/
        '''
        command = const.CMD_DOORSTATE_RRQ
        cmd_response = self.__send_command(command)
        if cmd_response.get('status'):
            return True
        else:
            return False

    def __str__(self):
        """
        for debug
        """
        return "ZK %s://%s:%s users[%i]:%i/%i fingers:%i/%i, records:%i/%i faces:%i/%i" % (
            "tcp" if self.tcp else "udp", self.__address[0], self.__address[1],
            self.user_packet_size, self.users, self.users_cap,
            self.fingers, self.fingers_cap,
            self.records, self.rec_cap,
            self.faces, self.faces_cap
        )

    def restart(self):
        """
        restart the device

        :return: bool
        """
        command = const.CMD_RESTART
        cmd_response = self.__send_command(command)
        if cmd_response.get('status'):
            self.is_connect = False
            self.next_uid = 1
            return True
        else:
            raise ZKErrorResponse("can't restart device")

    def write_lcd(self, line_number, text):
        """
        write text to LCD
        :param line_number: line number
        :param text: text to write
        """
        command = const.CMD_WRITE_LCD
        command_string = pack(b'<hb', line_number, 0) + b' ' + text.encode(self.encoding, errors='ignore')
        cmd_response = self.__send_command(command, command_string)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("can't write lcd")

    def clear_lcd(self):
        """
        clear LCD
        """
        command = const.CMD_CLEAR_LCD
        cmd_response = self.__send_command(command)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("can't clear lcd")

    def get_time(self):
        """
        :return: the machine's time
        """
        command = const.CMD_GET_TIME
        response_size = 1032
        cmd_response = self.__send_command(command, b'', response_size)
        if cmd_response.get('status'):
            return self.__decode_time(self.__data[:4])
        else:
            raise ZKErrorResponse("can't get time")

    def set_time(self, timestamp):
        """
        set Device time (pass datetime object)

        :param timestamp: python datetime object
        """
        command = const.CMD_SET_TIME
        command_string = pack(b'I', self.__encode_time(timestamp))
        cmd_response = self.__send_command(command, command_string)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("can't set time")

    def poweroff(self):
        """
        shutdown the machine
        """
        command = const.CMD_POWEROFF
        command_string = b''
        response_size = 1032
        cmd_response = self.__send_command(command, command_string, response_size)
        if cmd_response.get('status'):
            self.is_connect = False
            self.next_uid = 1
            return True
        else:
            raise ZKErrorResponse("can't poweroff")

    def refresh_data(self):
        command = const.CMD_REFRESHDATA
        cmd_response = self.__send_command(command)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("can't refresh data")

    def test_voice(self, index=0):
        """
        play test voice:\n
         0 Thank You\n
         1 Incorrect Password\n
         2 Access Denied\n
         3 Invalid ID\n
         4 Please try again\n
         5 Dupicate ID\n
         6 The clock is flow\n
         7 The clock is full\n
         8 Duplicate finger\n
         9 Duplicated punch\n
         10 Beep kuko\n
         11 Beep siren\n
         12 -\n
         13 Beep bell\n
         14 -\n
         15 -\n
         16 -\n
         17 -\n
         18 Windows(R) opening sound\n
         19 -\n
         20 Fingerprint not emolt\n
         21 Password not emolt\n
         22 Badges not emolt\n
         23 Face not emolt\n
         24 Beep standard\n
         25 -\n
         26 -\n
         27 -\n
         28 -\n
         29 -\n
         30 Invalid user\n
         31 Invalid time period\n
         32 Invalid combination\n
         33 Illegal Access\n
         34 Disk space full\n
         35 Duplicate fingerprint\n
         36 Fingerprint not registered\n
         37 -\n
         38 -\n
         39 -\n
         40 -\n
         41 -\n
         42 -\n
         43 -\n
         43 -\n
         45 -\n
         46 -\n
         47 -\n
         48 -\n
         49 -\n
         50 -\n
         51 Focus eyes on the green box\n
         52 -\n
         53 -\n
         54 -\n
         55 -\n

        :param index: int sound index
        :return: bool
        """
        command = const.CMD_TESTVOICE
        command_string = pack("I", index)
        cmd_response = self.__send_command(command, command_string)
        if cmd_response.get('status'):
            return True
        else:
            return False

    def set_user(self, uid=None, name='', privilege=0, password='', group_id='', user_id='', card=0):
        """
        create or update user by uid

        :param name: name ot the user
        :param privilege: check the const.py for reference
        :param password: int password
        :param group_id: group ID
        :param user_id: your own user ID
        :param card: card
        :return: bool
        """
        command = const.CMD_USER_WRQ
        if uid is None:
            uid = self.next_uid
            if not user_id:
                user_id = self.next_user_id
        if not user_id:
            user_id = str(uid) #ZK6 needs uid2 == uid
        #TODO: check what happens if name is missing...
        if privilege not in [const.USER_DEFAULT, const.USER_ADMIN]:
            privilege = const.USER_DEFAULT
        privilege = int(privilege)
        if self.user_packet_size == 28: #self.firmware == 6:
            if not group_id:
                group_id = 0
            try:
                command_string = pack('HB5s8sIxBHI', uid, privilege, password.encode(self.encoding, errors='ignore'), name.encode(self.encoding, errors='ignore'), card, int(group_id), 0, int(user_id))
            except Exception as e:
                if self.verbose: print("s_h Error pack: %s" % e)
                if self.verbose: print("Error pack: %s" % sys.exc_info()[0])
                raise ZKErrorResponse("Can't pack user")
        else:
            name_pad = name.encode(self.encoding, errors='ignore').ljust(24, b'\x00')[:24]
            card_str = pack('<I', int(card))[:4]
            command_string = pack('HB8s24s4sx7sx24s', uid, privilege, password.encode(self.encoding, errors='ignore'), name_pad, card_str, group_id.encode(), user_id.encode())
        response_size = 1024 #TODO check response?
        cmd_response = self.__send_command(command, command_string, response_size)
        if self.verbose: print("Response: %s" % cmd_response)
        if not cmd_response.get('status'):
            raise ZKErrorResponse("Can't set user")
        self.refresh_data()
        if self.next_uid == uid:
            self.next_uid += 1 # better recalculate again
        if self.next_user_id == user_id:
            self.next_user_id = str(self.next_uid)

    def save_user_template(self, user, fingers=[]):
        """
        save user and template

        :param user: user
        :param fingers: list of finger. (The maximum index 0-9)
        """
        if not isinstance(user, User):
            users = self.get_users()
            tusers = list(filter(lambda x: x.uid==user, users))
            if len(tusers) == 1:
                user = tusers[0]
            else:
                tusers = list(filter(lambda x: x.user_id==str(user), users))
                if len(tusers) == 1:
                    user = tusers[0]
                else:
                    raise ZKErrorResponse("Can't find user")
        if isinstance(fingers, Finger):
            fingers = [fingers]
        self.HR_save_usertemplates ([(user, fingers)])

    def HR_save_usertemplates(self, usertemplates):
        """
        save users and templates in high rate mode

        :param [user,[fingers]]
        """
        upack = b""
        fpack = b""
        table = b""
        fnum = 0x10
        tstart = 0
        for user, fingers in usertemplates:
            if not isinstance(user, User):
                raise ZKErrorResponse("Invalid user in usertemplates list")
            if self.user_packet_size == 28:
                upack += user.repack29()
            else:
                upack += user.repack73()
            for finger in fingers:
                if not isinstance(finger, Finger):
                    raise ZKErrorResponse("Invalid finger template in usertemplates list")
                tfp = finger.repack_only()
                table += pack("<bHbI", 2, user.uid, fnum + finger.fid, tstart)
                tstart += len(tfp)
                fpack += tfp
        head = pack("III", len(upack), len(table), len(fpack))
        packet = head + upack + table + fpack
        self._send_with_buffer(packet)
        command = const._CMD_SAVE_USERTEMPS
        command_string = pack('<IHH', 12,0,8)
        cmd_response = self.__send_command(command, command_string)
        if not cmd_response.get('status'):
            raise ZKErrorResponse("Can't save usertemplates")
        self.refresh_data()

    def _send_with_buffer(self, buffer):
        MAX_CHUNK = 1024
        size = len(buffer)
        self.free_data()
        command = const.CMD_PREPARE_DATA
        command_string = pack('I', size)
        cmd_response = self.__send_command(command, command_string)
        if not cmd_response.get('status'):
            raise ZKErrorResponse("Can't prepare data")
        remain = size % MAX_CHUNK
        packets = (size - remain) // MAX_CHUNK
        start = 0
        for _wlk in range(packets):
            self.__send_chunk(buffer[start:start+MAX_CHUNK])
            start += MAX_CHUNK
        if remain:
            self.__send_chunk(buffer[start:start+remain])

    def __send_chunk(self, command_string):
        command = const.CMD_DATA
        cmd_response = self.__send_command(command, command_string)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("Can't send chunk")

    def delete_user_template(self, uid=0, temp_id=0, user_id=''):
        """
        Delete specific template

        :param uid: user ID that are generated from device
        :param user_id: your own user ID
        :return: bool
        """
        if self.tcp and user_id:
            command = const._CMD_DEL_USER_TEMP
            command_string = pack('<24sB', str(user_id), temp_id)
            cmd_response = self.__send_command(command, command_string)
            if cmd_response.get('status'):
                return True
            else:
                return False # probably empty!
        if not uid:
            users = self.get_users()
            users = list(filter(lambda x: x.user_id==str(user_id), users))
            if not users:
                return False
            uid = users[0].uid
        command = const.CMD_DELETE_USERTEMP
        command_string = pack('hb', uid, temp_id)
        cmd_response = self.__send_command(command, command_string)
        if cmd_response.get('status'):
            return True #refres_data (1013)?
        else:
            return False # probably empty!

    def delete_user(self, uid=0, user_id=''):
        """
        delete specific user by uid or user_id

        :param uid: user ID that are generated from device
        :param user_id: your own user ID
        :return: bool
        """
        if not uid:
            users = self.get_users()
            users = list(filter(lambda x: x.user_id==str(user_id), users))
            if not users:
                return False
            uid = users[0].uid
        command = const.CMD_DELETE_USER
        command_string = pack('h', uid)
        cmd_response = self.__send_command(command, command_string)
        if not cmd_response.get('status'):
            raise ZKErrorResponse("Can't delete user")
        self.refresh_data()
        if uid == (self.next_uid - 1):
            self.next_uid = uid

    def get_user_template(self, uid = '', temp_id=0, user_id=''):
        """
        :param uid: user ID that are generated from device
        :param user_id: your own user ID
        :return: list Finger object of the selected user
        """
        if not uid:
            users = self.get_users()
            users = list(filter(lambda x: x.user_id==str(user_id), users))
            if not users:
                return False
            uid = users[0].uid
        for _retries in range(3):
            command = const._CMD_GET_USERTEMP # command secret!!! GET_USER_TEMPLATE
            command_string = pack('hb', uid, temp_id)
            response_size = 1024 + 8
            cmd_response = self.__send_command(command, command_string, response_size)
            data = self.__recieve_chunk()
            if data is not None:
                resp = data[:-1]
                if resp[-6:] == b'\x00\x00\x00\x00\x00\x00': # padding? bug?
                    resp = resp[:-6]
                return Finger(uid, temp_id, 1, resp)
            if self.verbose: print ("retry get_user_template")
        else:
            if self.verbose: print ("Can't read/find finger")
            return None

    def get_templates(self):
        """
        :return: list of Finger object
        """
        self.read_sizes()
        if self.fingers == 0:
            return []
        templates = []
        templatedata, size = self.read_with_buffer(const.CMD_DB_RRQ, const.FCT_FINGERTMP)
        if size < 4:
            if self.verbose: print("WRN: no user data")
            return []
        total_size = unpack('i', templatedata[0:4])[0]
        if self.verbose: print ("get template total size {}, size {} len {}".format(total_size, size, len(templatedata)))
        templatedata = templatedata[4:]
        while total_size:
            size, uid, fid, valid = unpack('HHbb',templatedata[:6])
            template = unpack("%is" % (size-6), templatedata[6:size])[0]
            finger = Finger(uid, fid, valid, template)
            if self.verbose: print(finger)
            templates.append(finger)
            templatedata = templatedata[size:]
            total_size -= size
        return templates

    def get_users(self):
        """
        :return: list of User object
        """
        self.read_sizes()
        if self.users == 0:
            self.next_uid = 1
            self.next_user_id='1'
            return []
        users = []
        max_uid = 0
        userdata, size = self.read_with_buffer(const.CMD_USERTEMP_RRQ, const.FCT_USER)
        if self.verbose: print("user size {} (= {})".format(size, len(userdata)))
        if size <= 4:
            print("WRN: missing user data")
            return []
        total_size = unpack("I",userdata[:4])[0]
        self.user_packet_size = total_size / self.users
        if not self.user_packet_size in [28, 72]:
            if self.verbose: print("WRN packet size would be  %i" % self.user_packet_size)
        userdata = userdata[4:]
        if self.user_packet_size == 28:
            while len(userdata) >= 28:
                uid, privilege, password, name, card, group_id, timezone, user_id = unpack('<HB5s8sIxBhI',userdata.ljust(28, b'\x00')[:28])
                if uid > max_uid: max_uid = uid
                password = (password.split(b'\x00')[0]).decode(self.encoding, errors='ignore')
                name = (name.split(b'\x00')[0]).decode(self.encoding, errors='ignore').strip()
                group_id = str(group_id)
                user_id = str(user_id)
                #TODO: check card value and find in ver8
                if not name:
                    name = "NN-%s" % user_id
                user = User(uid, name, privilege, password, group_id, user_id, card)
                users.append(user)
                if self.verbose: print("[6]user:",uid, privilege, password, name, card, group_id, timezone, user_id)
                userdata = userdata[28:]
        else:
            while len(userdata) >= 72:
                uid, privilege, password, name, card, group_id, user_id = unpack('<HB8s24sIx7sx24s', userdata.ljust(72, b'\x00')[:72])
                password = (password.split(b'\x00')[0]).decode(self.encoding, errors='ignore')
                name = (name.split(b'\x00')[0]).decode(self.encoding, errors='ignore').strip()
                group_id = (group_id.split(b'\x00')[0]).decode(self.encoding, errors='ignore').strip()
                user_id = (user_id.split(b'\x00')[0]).decode(self.encoding, errors='ignore')
                if uid > max_uid: max_uid = uid
                if not name:
                    name = "NN-%s" % user_id
                user = User(uid, name, privilege, password, group_id, user_id, card)
                users.append(user)
                userdata = userdata[72:]
        max_uid += 1
        self.next_uid = max_uid
        self.next_user_id = str(max_uid)
        while True:
            if any(u for u in users if u.user_id == self.next_user_id):
                max_uid += 1
                self.next_user_id = str(max_uid)
            else:
                break
        return users

    def cancel_capture(self):
        """
        cancel capturing finger

        :return: bool
        """
        command = const.CMD_CANCELCAPTURE
        cmd_response = self.__send_command(command)
        return bool(cmd_response.get('status'))

    def verify_user(self):
        """
        start verify finger mode (after capture)

        :return: bool
        """
        command = const.CMD_STARTVERIFY
        cmd_response = self.__send_command(command)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("Cant Verify")

    def reg_event(self, flags):
        """
        reg events
        """
        command = const.CMD_REG_EVENT
        command_string = pack ("I", flags)
        cmd_response = self.__send_command(command, command_string)
        if not cmd_response.get('status'):
            raise ZKErrorResponse("cant' reg events %i" % flags)

    def set_sdk_build_1(self):
        command = const.CMD_OPTIONS_WRQ
        command_string = b"SDKBuild=1"
        cmd_response = self.__send_command(command, command_string)
        if not cmd_response.get('status'):
            return False
        return True

    def enroll_user(self, uid=0, temp_id=0, user_id=''):
        """
        start enroll user

        :param uid: uid
        :param temp_id: template id
        :param user_id: user ID
        :return: bool
        """
        command = const.CMD_STARTENROLL
        done = False
        if  not user_id:
            users = self.get_users()
            users = list(filter(lambda x: x.uid==uid, users))
            if len(users) >= 1:
                user_id = users[0].user_id
            else:
                return False
        if self.tcp:
            command_string = pack('<24sbb',str(user_id).encode(), temp_id, 1)
        else:
            command_string = pack('<Ib', int(user_id), temp_id)
        self.cancel_capture()
        cmd_response = self.__send_command(command, command_string)
        if not cmd_response.get('status'):
            raise ZKErrorResponse("Cant Enroll user #%i [%i]" %(uid, temp_id))
        self.__sock.settimeout(60)
        attempts = 3
        while attempts:
            if self.verbose: print("A:%i esperando primer regevent" % attempts)
            data_recv = self.__sock.recv(1032)
            self.__ack_ok()
            if self.verbose: print(codecs.encode(data_recv,'hex'))
            if self.tcp:
                if len(data_recv) > 16:
                    res = unpack("H", data_recv.ljust(24,b"\x00")[16:18])[0]
                    if self.verbose: print("res %i" % res)
                    if res == 0 or res == 6 or res == 4:
                        if self.verbose: print ("posible timeout  o reg Fallido")
                        break
            else:
                if len(data_recv) > 8:
                    res = unpack("H", data_recv.ljust(16,b"\x00")[8:10])[0]
                    if self.verbose: print("res %i" % res)
                    if res == 6 or res == 4:
                        if self.verbose: print ("posible timeout")
                        break
            if self.verbose: print ("A:%i esperando 2do regevent" % attempts)
            data_recv = self.__sock.recv(1032)
            self.__ack_ok()
            if self.verbose: print (codecs.encode(data_recv, 'hex'))
            if self.tcp:
                if len(data_recv) > 8:
                    res = unpack("H", data_recv.ljust(24,b"\x00")[16:18])[0]
                    if self.verbose: print("res %i" % res)
                    if res == 6 or res == 4:
                        if self.verbose: print ("posible timeout  o reg Fallido")
                        break
                    elif res == 0x64:
                        if self.verbose: print ("ok, continue?")
                        attempts -= 1
            else:
                if len(data_recv) > 8:
                    res = unpack("H", data_recv.ljust(16,b"\x00")[8:10])[0]
                    if self.verbose: print("res %i" % res)
                    if res == 6 or res == 4:
                        if self.verbose: print ("posible timeout  o reg Fallido")
                        break
                    elif res == 0x64:
                        if self.verbose: print ("ok, continue?")
                        attempts -= 1
        if attempts == 0:
            data_recv = self.__sock.recv(1032)
            self.__ack_ok()
            if self.verbose: print (codecs.encode(data_recv, 'hex'))
            if self.tcp:
                res = unpack("H", data_recv.ljust(24,b"\x00")[16:18])[0]
            else:
                res = unpack("H", data_recv.ljust(16,b"\x00")[8:10])[0]
            if self.verbose: print("res %i" % res)
            if res == 5:
                if self.verbose: print ("finger duplicate")
            if res == 6 or res == 4:
                if self.verbose: print ("posible timeout")
            if res  == 0:
                size = unpack("H", data_recv.ljust(16,b"\x00")[10:12])[0]
                pos = unpack("H", data_recv.ljust(16,b"\x00")[12:14])[0]
                if self.verbose: print("enroll ok", size, pos)
                done = True
        self.__sock.settimeout(self.__timeout)
        self.reg_event(0) # TODO: test
        self.cancel_capture()
        self.verify_user()
        return done

    def live_capture(self, new_timeout=10):
        """
        try live capture of events
        """
        was_enabled = self.is_enabled
        users = self.get_users()
        self.cancel_capture()
        self.verify_user()
        if not self.is_enabled:
            self.enable_device()
        if self.verbose: print ("start live_capture")
        self.reg_event(const.EF_ATTLOG)
        self.__sock.settimeout(new_timeout)
        self.end_live_capture = False
        while not self.end_live_capture:
            try:
                if self.verbose: print ("esperando event")
                data_recv = self.__sock.recv(1032)
                self.__ack_ok()
                if self.tcp:
                    size = unpack('<HHI', data_recv[:8])[2]
                    header = unpack('HHHH', data_recv[8:16])
                    data = data_recv[16:]
                else:
                    size = len(data_recv)
                    header = unpack('<4H', data_recv[:8])
                    data = data_recv[8:]
                if not header[0] == const.CMD_REG_EVENT:
                    if self.verbose: print("not event! %x" % header[0])
                    continue
                if not len(data):
                    if self.verbose: print ("empty")
                    continue
                while len(data) >= 10:
                    if len(data) == 10:
                        user_id, status, punch, timehex = unpack('<HBB6s', data)
                        data = data[10:]
                    elif len(data) == 12:
                        user_id, status, punch, timehex = unpack('<IBB6s', data)
                        data = data[12:]
                    elif len(data) == 14:
                        user_id, status, punch, timehex, _other = unpack('<HBB6s4s', data)
                        data = data[14:]
                    elif len(data) == 32:
                        user_id,  status, punch, timehex = unpack('<24sBB6s', data[:32])
                        data = data[32:]
                    elif len(data) == 36:
                        user_id,  status, punch, timehex, _other = unpack('<24sBB6s4s', data[:36])
                        data = data[36:]
                    elif len(data) == 37:
                        user_id,  status, punch, timehex, _other = unpack('<24sBB6s5s', data[:37])
                        data = data[37:]
                    elif len(data) >= 52:
                        user_id,  status, punch, timehex, _other = unpack('<24sBB6s20s', data[:52])
                        data = data[52:]
                    if isinstance(user_id, int):
                        user_id = str(user_id)
                    else:
                        user_id = (user_id.split(b'\x00')[0]).decode(errors='ignore')
                    timestamp = self.__decode_timehex(timehex)
                    tuser = list(filter(lambda x: x.user_id == user_id, users))
                    if not tuser:
                        uid = int(user_id)
                    else:
                        uid = tuser[0].uid
                    yield Attendance(user_id, timestamp, status, punch, uid)
            except timeout:
                if self.verbose: print ("time out")
                yield None # return to keep watching
            except (KeyboardInterrupt, SystemExit):
                if self.verbose: print ("break")
                break
        if self.verbose: print ("exit gracefully")
        self.__sock.settimeout(self.__timeout)
        self.reg_event(0)
        if not was_enabled:
            self.disable_device()

    def clear_data(self):
        """
        clear all data (included: user, attendance report, finger database)

        :return: bool
        """
        command = const.CMD_CLEAR_DATA
        command_string = b''
        cmd_response = self.__send_command(command, command_string)
        if cmd_response.get('status'):
            self.next_uid = 1
            return True
        else:
            raise ZKErrorResponse("can't clear data")

    def __recieve_tcp_data(self, data_recv, size):
        """ data_recv, raw tcp packet
         must analyze tcp_length

         must return data, broken
         """
        data = []
        tcp_length = self.__test_tcp_top(data_recv)
        if self.verbose: print ("tcp_length {}, size {}".format(tcp_length, size))
        if tcp_length <= 0:
            if self.verbose: print ("Incorrect tcp packet")
            return None, b""
        if (tcp_length - 8) < size:
            if self.verbose: print ("tcp length too small... retrying")
            resp, bh = self.__recieve_tcp_data(data_recv, tcp_length - 8)
            data.append(resp)
            size -= len(resp)
            if self.verbose: print ("new tcp DATA packet to fill misssing {}".format(size))
            data_recv = bh + self.__sock.recv(size + 16 )
            if self.verbose: print ("new tcp DATA starting with {} bytes".format(len(data_recv)))
            resp, bh = self.__recieve_tcp_data(data_recv, size)
            data.append(resp)
            if self.verbose: print ("for misssing {} recieved {} with extra {}".format(size, len(resp), len(bh)))
            return b''.join(data), bh
        recieved = len(data_recv)
        if self.verbose: print ("recieved {}, size {}".format(recieved, size))
        response = unpack('HHHH', data_recv[8:16])[0]
        if recieved >= (size + 32):
            if response == const.CMD_DATA:
                resp = data_recv[16 : size + 16]
                if self.verbose: print ("resp complete len {}".format(len(resp)))
                return resp, data_recv[size + 16:]
            else:
                if self.verbose: print("incorrect response!!! {}".format(response))
                return None, b""
        else:
            if self.verbose: print ("try DATA incomplete (actual valid {})".format(recieved-16))
            data.append(data_recv[16 : size + 16 ])
            size -= recieved - 16
            broken_header = b""
            if size < 0:
                broken_header = data_recv[size:]
                if self.verbose: print ("broken", (broken_header).encode('hex'))
            if size > 0:
                data_recv = self.__recieve_raw_data(size)
                data.append(data_recv)
            return b''.join(data), broken_header

    def __recieve_raw_data(self, size):
        """ partial data ? """
        data = []
        if self.verbose: print ("expecting {} bytes raw data".format(size))
        while size > 0:
            data_recv = self.__sock.recv(size)
            recieved = len(data_recv)
            if self.verbose: print ("partial recv {}".format(recieved))
            if recieved < 100 and self.verbose: print ("   recv {}".format(codecs.encode(data_recv, 'hex')))
            data.append(data_recv)
            size -= recieved
            if self.verbose: print ("still need {}".format(size))
        return b''.join(data)

    def __recieve_chunk(self):
        """ recieve a chunk """
        if self.__response == const.CMD_DATA:
            if self.tcp:
                if self.verbose: print ("_rc_DATA! is {} bytes, tcp length is {}".format(len(self.__data), self.__tcp_length))
                if len(self.__data) < (self.__tcp_length - 8):
                    need = (self.__tcp_length - 8) - len(self.__data)
                    if self.verbose: print ("need more data: {}".format(need))
                    more_data = self.__recieve_raw_data(need)
                    return b''.join([self.__data, more_data])
                else:
                    if self.verbose: print ("Enough data")
                    return self.__data
            else:
                if self.verbose: print ("_rc len is {}".format(len(self.__data)))
                return self.__data
        elif self.__response == const.CMD_PREPARE_DATA:
            data = []
            size = self.__get_data_size()
            if self.verbose: print ("recieve chunk: prepare data size is {}".format(size))
            if self.tcp:
                if len(self.__data) >= (8 + size):
                    data_recv = self.__data[8:]
                else:
                    data_recv = self.__data[8:] + self.__sock.recv(size + 32)
                resp, broken_header = self.__recieve_tcp_data(data_recv, size)
                data.append(resp)
                # get CMD_ACK_OK
                if len(broken_header) < 16:
                    data_recv = broken_header + self.__sock.recv(16)
                else:
                    data_recv = broken_header
                if len(data_recv) < 16:
                    print ("trying to complete broken ACK %s /16" % len(data_recv))
                    if self.verbose: print (data_recv.encode('hex'))
                    data_recv += self.__sock.recv(16 - len(data_recv)) #TODO: CHECK HERE_!
                if not self.__test_tcp_top(data_recv):
                    if self.verbose: print ("invalid chunk tcp ACK OK")
                    return None
                response = unpack('HHHH', data_recv[8:16])[0]
                if response == const.CMD_ACK_OK:
                    if self.verbose: print ("chunk tcp ACK OK!")
                    return b''.join(data)
                if self.verbose: print("bad response %s" % data_recv)
                if self.verbose: print (codecs.encode(data,'hex'))
                return None

                return resp
            while True:
                data_recv = self.__sock.recv(1024+8)
                response = unpack('<4H', data_recv[:8])[0]
                if self.verbose: print ("# packet response is: {}".format(response))
                if response == const.CMD_DATA:
                    data.append(data_recv[8:])
                    size -= 1024
                elif response == const.CMD_ACK_OK:
                    break
                else:
                    if self.verbose: print ("broken!")
                    break
                if self.verbose: print ("still needs %s" % size)
            return b''.join(data)
        else:
            if self.verbose: print ("invalid response %s" % self.__response)
            return None

    def __read_chunk(self, start, size):
        """
        read a chunk from buffer
        """
        for _retries in range(3):
            command = const._CMD_READ_BUFFER
            command_string = pack('<ii', start, size)
            if self.tcp:
                response_size = size + 32
            else:
                response_size = 1024 + 8
            cmd_response = self.__send_command(command, command_string, response_size)
            data = self.__recieve_chunk()
            if data is not None:
                return data
        else:
            raise ZKErrorResponse("can't read chunk %i:[%i]" % (start, size))

    def read_with_buffer(self, command, fct=0 ,ext=0):
        """
        Test read info with buffered command (ZK6: 1503)
        """
        if self.tcp:
            MAX_CHUNK = 0xFFc0
        else:
            MAX_CHUNK = 16 * 1024
        command_string = pack('<bhii', 1, command, fct, ext)
        if self.verbose: print ("rwb cs", command_string)
        response_size = 1024
        data = []
        start = 0
        cmd_response = self.__send_command(const._CMD_PREPARE_BUFFER, command_string, response_size)
        if not cmd_response.get('status'):
            raise ZKErrorResponse("RWB Not supported")
        if cmd_response['code'] == const.CMD_DATA:
            if self.tcp:
                if self.verbose: print ("DATA! is {} bytes, tcp length is {}".format(len(self.__data), self.__tcp_length))
                if len(self.__data) < (self.__tcp_length - 8):
                    need = (self.__tcp_length - 8) - len(self.__data)
                    if self.verbose: print ("need more data: {}".format(need))
                    more_data = self.__recieve_raw_data(need)
                    return b''.join([self.__data, more_data]), len(self.__data) + len(more_data)
                else:
                    if self.verbose: print ("Enough data")
                    size = len(self.__data)
                    return self.__data, size
            else:
                size = len(self.__data)
                return self.__data, size
        size = unpack('I', self.__data[1:5])[0]
        if self.verbose: print ("size fill be %i" % size)
        remain = size % MAX_CHUNK
        packets = (size-remain) // MAX_CHUNK # should be size /16k
        if self.verbose: print ("rwb: #{} packets of max {} bytes, and extra {} bytes remain".format(packets, MAX_CHUNK, remain))
        for _wlk in range(packets):
            data.append(self.__read_chunk(start,MAX_CHUNK))
            start += MAX_CHUNK
        if remain:
            data.append(self.__read_chunk(start, remain))
            start += remain
        self.free_data()
        if self.verbose: print ("_read w/chunk %i bytes" % start)
        return b''.join(data), start

    def get_attendance(self):
        """
        return attendance record

        :return: List of Attendance object
        """
        self.read_sizes()
        if self.records == 0:
            return []
        users = self.get_users()
        if self.verbose: print (users)
        attendances = []
        attendance_data, size = self.read_with_buffer(const.CMD_ATTLOG_RRQ)
        if size < 4:
            if self.verbose: print ("WRN: no attendance data")
            return []
        total_size = unpack("I", attendance_data[:4])[0]
        record_size = total_size // self.records
        if self.verbose: print ("record_size is ", record_size)
        attendance_data = attendance_data[4:]
        if record_size == 8:
            while len(attendance_data) >= 8:
                uid, status, timestamp, punch = unpack('HB4sB', attendance_data.ljust(8, b'\x00')[:8])
                if self.verbose: print (codecs.encode(attendance_data[:8], 'hex'))
                attendance_data = attendance_data[8:]
                tuser = list(filter(lambda x: x.uid == uid, users))
                if not tuser:
                    user_id = str(uid)
                else:
                    user_id = tuser[0].user_id
                timestamp = self.__decode_time(timestamp)
                attendance = Attendance(user_id, timestamp, status, punch, uid)
                attendances.append(attendance)
        elif record_size == 16:
            while len(attendance_data) >= 16:
                user_id, timestamp, status, punch, reserved, workcode = unpack('<I4sBB2sI', attendance_data.ljust(16, b'\x00')[:16])
                user_id = str(user_id)
                if self.verbose: print(codecs.encode(attendance_data[:16], 'hex'))
                attendance_data = attendance_data[16:]
                tuser = list(filter(lambda x: x.user_id == user_id, users))
                if not tuser:
                    if self.verbose: print("no uid {}", user_id)
                    uid = str(user_id)
                    tuser = list(filter(lambda x: x.uid == user_id, users))
                    if not tuser:
                        uid = str(user_id)
                    else:
                        uid = tuser[0].uid
                        user_id = tuser[0].user_id
                else:
                    uid = tuser[0].uid
                timestamp = self.__decode_time(timestamp)
                attendance = Attendance(user_id, timestamp, status, punch, uid)
                attendances.append(attendance)
        else:
            while len(attendance_data) >= 40:
                uid, user_id, status, timestamp, punch, space = unpack('<H24sB4sB8s', attendance_data.ljust(40, b'\x00')[:40])
                if self.verbose: print (codecs.encode(attendance_data[:40], 'hex'))
                user_id = (user_id.split(b'\x00')[0]).decode(errors='ignore')
                timestamp = self.__decode_time(timestamp)

                attendance = Attendance(user_id, timestamp, status, punch, uid)
                attendances.append(attendance)
                attendance_data = attendance_data[record_size:]
        return attendances

    def clear_attendance(self):
        """
        clear all attendance record

        :return: bool
        """
        command = const.CMD_CLEAR_ATTLOG
        cmd_response = self.__send_command(command)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("Can't clear response")
