# -*- coding: utf-8 -*-
import sys
from datetime import datetime
from socket import AF_INET, SOCK_DGRAM, socket
from struct import pack, unpack

from zk import const
from zk.attendance import Attendance
from zk.exception import ZKErrorResponse, ZKNetworkError
from zk.user import User
from zk.finger import Finger

def make_commkey(key, session_id, ticks=50):
    """take a password and session_id and scramble them to send to the time
    clock.
    copied from commpro.c - MakeKey"""
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

class ZK(object):

    is_connect = False

    __data_recv = None
    __sesion_id = 0
    __reply_id = 0

    def __init__(self, ip, port=4370, timeout=60, password=0, firmware=8):
        self.is_connect = False
        self.__address = (ip, port)
        self.__sock = socket(AF_INET, SOCK_DGRAM)
        self.__sock.settimeout(timeout)
        self.__password = password # passint
        self.__firmware = int(firmware) #TODO check minor version?
        self.users = 0
        self.fingers = 0
        self.records = 0
        self.dummy = 0
        self.cards = 0
        self.fingers_cap = 0
        self.users_cap = 0
        self.rec_cap = 0
        self.fingers_av = 0
        self.users_av = 0
        self.rec_av = 0
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
        #print "decode from  %s "% format(t, '04x')
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

    def __encode_time(self, t):
        """Encode a timestamp so that it can be read on the timeclock
        """
        # formula taken from zkemsdk.c - EncodeTime
        # can also be found in the technical manual
        d = (
            ((t.year % 100) * 12 * 31 + ((t.month - 1) * 31) + t.day - 1) *
            (24 * 60 * 60) + (t.hour * 60 + t.minute) * 60 + t.second
        )
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
        self.__sesion_id = unpack('HHHH', self.__data_recv[:8])[2]
        if cmd_response.get('code')==const.CMD_ACK_UNAUTH:
            #print "try auth"
            command_string = make_commkey(self.__password,self.__sesion_id)
            cmd_response = self.__send_command(const.CMD_AUTH, command_string , checksum, self.__sesion_id, self.__reply_id, response_size)
        if cmd_response.get('status'):
            self.is_connect = True
            # set the session iduid, privilege, password, name, card, group_id, timezone, user_id = unpack('HB5s8s5sBhI',userdata.ljust(28)[:28])
            return self
        else:
            print "connect err {} ".format(cmd_response["code"])
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
            self.is_connect = False
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

    def get_platform(self):
        '''
        return the serial number
        '''
        command = const.CMD_OPTIONS_RRQ
        command_string = '~Platform'
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            platform = self.__data_recv[8:].split('=')[-1].split('\x00')[0]
            return platform
        else:
            raise ZKErrorResponse("Invalid response")

    def get_device_name(self):
        '''
        return the serial number
        '''
        command = const.CMD_OPTIONS_RRQ
        command_string = '~DeviceName'
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            device = self.__data_recv[8:].split('=')[-1].split('\x00')[0]
            return device
        else:
            raise ZKErrorResponse("Invalid response")

    def get_pin_width(self):
        '''
        return the serial number
        '''
        command = const.CMD_GET_PINWIDTH
        command_string = ' P'
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            width = self.__data_recv[8:].split('\x00')[0]
            return bytearray(width)[0]
        else:
            raise ZKErrorResponse("Invalid response")

    def free_data(self):
        """ clear buffer"""
        command = const.CMD_FREE_DATA
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

    def read_sizes(self):
        """ read sizes """
        command = const.CMD_GET_FREE_SIZES
        command_string = ''
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            fields = unpack('iiiiiiiiiiiiiiiiiiii', self.__data_recv[8:])
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
            #TODO: get faces size...

            return True
        else:
            raise ZKErrorResponse("Invalid response")

    def __str__(self):
        """ for debug"""
        return "ZK%i adr:%s:%s users:%i/%i fingers:%i/%i, records:%i/%i" % (
            self.__firmware, self.__address[0], self.__address[1],
            self.users, self.users_cap, self.fingers, self.fingers_cap,
            self.records, self.rec_cap
        )

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

    def get_time(self):
        """obtener la hora del equipo"""
        command = const.CMD_GET_TIME
        command_string = ''
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 1032

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            return self.__decode_time(self.__data_recv[8:12])
        else:
            raise ZKErrorResponse("Invalid response")

    def set_time(self, timestamp):
        """ colocar la hora del sistema al zk """
        command = const.CMD_SET_TIME
        command_string = pack(b'I', self.__encode_time(timestamp))
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
        response_size = 1032

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("Invalid response")

    def test_voice(self):
        '''
        play test voice
        '''
        command = const.CMD_TESTVOICEuid, privilege, password, name, card, group_id, timezone, user_id = unpack('HB5s8s5sBhI',userdata.ljust(28)[:28])
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

    def set_user(self, uid, name, privilege=0, password='', group_id='', user_id='', card=0):
        '''
        create or update user by uid
        '''
        command = const.CMD_USER_WRQ
        if not user_id:
            user_id = str(uid) #ZK6 needs uid2 == uid
        #uid = chr(uid % 256) + chr(uid >> 8)
        if privilege not in [const.USER_DEFAULT, const.USER_ADMIN]:
            privilege = const.USER_DEFAULT
        privilege = chr(privilege)
        if self.__firmware == 6:
            print "uid : %i" % uid
            print "pri : %c" % privilege
            print "pass: %s" % str(password)
            print "name: %s" % str(name)
            print type(name)
            print "group %i" % int(group_id)
            print "uid2: %i" % int(user_id)
            try:
                command_string = pack('Hc5s8s5sBHI', uid, privilege, str(password), str(name), chr(0), int(group_id), 0, int(user_id))
                print "cmd : %s" % command_string
            except Exception, e:
                print "s_h Error pack: %s" % e
                print "Error pack: %s" % sys.exc_info()[0]
                raise ZKErrorResponse("Invalid response")
        else:
            command_string = pack('Hc8s28sc7sx24s', uid, privilege, password, name, chr(0), group_id, user_id)
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            return True
        else:
            raise ZKErrorResponse("Invalid response")

    def delete_user_template(self, uid, temp_id):
        """
        Delete specific template
        """
        command = const.CMD_DELETE_USERTEMP
        command_string = pack('hb', uid, temp_id)
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 1024

        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        if cmd_response.get('status'):
            return True #refres_data (1013)?
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

    def get_user_template(self, uid, temp_id):
        command = 88 # comando secreto!!!
        command_string = pack('hb', uid, temp_id)
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 1024
        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        data = []
        if not cmd_response.get('status'):
            raise ZKErrorResponse("Invalid response")
        #else
        if cmd_response.get('code') == const.CMD_PREPARE_DATA:
            bytes = self.__get_data_size() #TODO: check with size
            size = bytes
            while True: #limitado por respuesta no por tamaño
                data_recv = self.__sock.recv(1032)
                response = unpack('HHHH', data_recv[:8])[0]
                #print "# %s packet response is: %s" % (pac, response)
                if response == const.CMD_DATA:
                    data.append(data_recv[8:]) #header turncated
                    bytes -= 1024
                elif response == const.CMD_ACK_OK:
                    break #without problem.
                else:
                    #truncado! continuar?
                    #print "broken!"
                    break
                #print "still needs %s" % bytes
        data = ''.join(data)
        #uid 32 fing 03, starts with 4d-9b-53-53-32-31
        return Finger(size + 6, uid, temp_id, 1, data) # TODO: confirm

    def get_templates(self):
        """ return array of all fingers """
        templates = []
        templatedata, size = self.read_with_buffer(const.CMD_DB_RRQ, const.FCT_FINGERTMP)
        if size < 4:
            print "WRN: no user data" # debug
            return []
        total_size = unpack('i', templatedata[0:4])[0]
        templatedata = templatedata[4:] #total size not used
        if self.__firmware == 6: #tested!
            while total_size:
                size, uid, fid, valid = unpack('HHbb',templatedata[:6])
                template = unpack("%is" % (size-6), templatedata[6:size])[0]
                finger = Finger(size, uid, fid, valid, template)
                print finger # test
                templates.append(finger)
                templatedata = templatedata[size:]
                total_size -= size
        else: # TODO: test!!!
            while total_size:
                size, uid, fid, valid = unpack('HHbb',templatedata[:6])
                template = unpack("%is" % (size-6), templatedata[6:size])[0]
                finger = Finger(size, uid, fid, valid, template)
                print finger # test
                templates.append(finger)
                templatedata = templatedata[(size):]
                total_size -= size
        return templates

    def get_users(self):
        """ return all user """
        users = []
        userdata, size = self.read_with_buffer(const.CMD_USERTEMP_RRQ, const.FCT_USER)
        print "user size %i" % size
        if size < 4:
            print "WRN: no user data" # debug
            return []
        userdata = userdata[4:] #total size not used
        if self.__firmware == 6:
            while len(userdata) >= 28:
                uid, privilege, password, name, card, group_id, timezone, user_id = unpack('HB5s8s5sBhI',userdata.ljust(28)[:28])
                password = unicode(password.split('\x00')[0], errors='ignore')
                name = unicode(name.split('\x00')[0], errors='ignore').strip()
                card = unpack('Q', card.ljust(8,'\x00'))[0] #or hex value?
                group_id = str(group_id)
                user_id = str(user_id)
                #TODO: check card value and find in ver8                                
                if not name:
                    name = "NN-%s" % user_id
                user = User(uid, name, privilege, password, group_id, user_id)
                users.append(user)
                print "[6]user:",uid, privilege, password, name, card, group_id, timezone, user_id
                userdata = userdata[28:]
        else:
            while len(userdata) >= 72:
                uid, privilege, password, name, sparator, group_id, user_id = unpack('Hc8s28sc7sx24s', userdata.ljust(72)[:72])
                #u1 = int(uid[0].encode("hex"), 16)
                #u2 = int(uid[1].encode("hex"), 16)
                #uid = u1 + (u2 * 256)
                privilege = int(privilege.encode("hex"), 16)
                password = unicode(password.split('\x00')[0], errors='ignore')
                name = unicode(name.split('\x00')[0], errors='ignore').strip()
                group_id = unicode(group_id.split('\x00')[0], errors='ignore').strip()
                user_id = unicode(user_id.split('\x00')[0], errors='ignore')
                if not name:
                    name = "NN-%s" % user_id
                user = User(uid, name, privilege, password, group_id, user_id)
                users.append(user)
                userdata = userdata[72:]
        return users
        
    def _get_users(self):
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
        pac = 0
        if cmd_response.get('status'):
            if cmd_response.get('code') == const.CMD_PREPARE_DATA:
                bytes = self.__get_data_size()
                userdata = []
                while True:
                    data_recv = self.__sock.recv(1032)
                    response = unpack('HHHH', data_recv[:8])[0]
                    if response == const.CMD_DATA:
                        pac += 1
                        userdata.append(data_recv[8:]) #header turncated
                        bytes -= 1024
                    elif response == const.CMD_ACK_OK:
                        break #without problem.
                    else:
                        #truncado! continuar?
                        #print "broken! with %s" % response
                        #print "user still needs %s" % bytes
                        break
                    
                if response == const.CMD_ACK_OK:
                    if userdata:
                        # The first 4 bytes don't seem to be related to the user
                        userdata = ''.join(userdata)
                        userdata = userdata[4:]
                        if self.__firmware == 6:
                            while len(userdata) >= 28:
                                uid, privilege, password, name, card, group_id, timezone, user_id = unpack('HB5s8s5sBhI',userdata.ljust(28)[:28])
                                password = unicode(password.split('\x00')[0], errors='ignore')
                                name = unicode(name.split('\x00')[0], errors='ignore').strip()
                                card = unpack('Q', card.ljust(8,'\x00'))[0] #or hex value?
                                group_id = str(group_id)
                                user_id = str(user_id)
                                #TODO: check card value and find in ver8                                
                                if not name:
                                    name = "NN-%s" % user_id
                                user = User(uid, name, privilege, password, group_id, user_id)
                                users.append(user)
                                print "[6]user:",uid, privilege, password, name, card, group_id, timezone, user_id
                                userdata = userdata[28:]
                        else:
                            while len(userdata) >= 72:
                                uid, privilege, password, name, sparator, group_id, user_id = unpack('Hc8s28sc7sx24s', userdata.ljust(72)[:72])
                                #u1 = int(uid[0].encode("hex"), 16)
                                #u2 = int(uid[1].encode("hex"), 16)
                                #uid = u1 + (u2 * 256)
                                privilege = int(privilege.encode("hex"), 16)
                                password = unicode(password.split('\x00')[0], errors='ignore')
                                name = unicode(name.split('\x00')[0], errors='ignore').strip()
                                group_id = unicode(group_id.split('\x00')[0], errors='ignore').strip()
                                user_id = unicode(user_id.split('\x00')[0], errors='ignore')
                                if not name:
                                    name = "NN-%s" % user_id
                                user = User(uid, name, privilege, password, group_id, user_id)
                                users.append(user)

                                userdata = userdata[72:]
                        self.free_data()
                else:
                    raise ZKErrorResponse("Invalid response")
        return users

    def cancel_capture(self):
        '''
        cancel capturing finger
        '''
        command = const.CMD_CANCELCAPTURE
        command_string = ''
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 8
        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        return bool(cmd_response.get('status'))

    def verify_user(self):
        '''
        verify finger
        '''
        command = const.CMD_STARTVERIFY
        # uid = chr(uid % 256) + chr(uid >> 8)
        cmd_response = self.__send_command(command=command)
        print cmd_response

    def enroll_user(self, uid, temp_id=0):
        '''
        start enroll user
        '''
        command = const.CMD_STARTENROLL
        command_string = pack('hhb', uid, 0, temp_id) # el 0 es misterio
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

    def __read_chunk(self, start, size):
        """ read a chunk from buffer """
        command = 1504 #CMD_READ_BUFFER
        command_string = pack('<ii', start, size)
        #print "rc cs", command_string
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 1024
        cmd_response = self.__send_command(command, command_string, checksum, session_id, reply_id, response_size)
        data = []
        if not cmd_response.get('status'):
            raise ZKErrorResponse("Invalid response")
        #else
        if cmd_response.get('code') == const.CMD_PREPARE_DATA:
            bytes = self.__get_data_size() #TODO: check with size
            while True: #limitado por respuesta no por tamaño
                data_recv = self.__sock.recv(1032)
                response = unpack('HHHH', data_recv[:8])[0]
                #print "# %s packet response is: %s" % (pac, response)
                if response == const.CMD_DATA:
                    data.append(data_recv[8:]) #header turncated
                    bytes -= 1024
                elif response == const.CMD_ACK_OK:
                    break #without problem.
                else:
                    #truncado! continuar?
                    #print "broken!"
                    break
                #print "still needs %s" % bytes
        return ''.join(data)

    def read_with_buffer(self, command, fct=0 ,ext=0):
        """ Test read info with buffered command (ZK6: 1503) """
        MAX_CHUNK = 16 * 1204
        command_string = pack('<bhii', 1, command, fct, ext)
        #print "rwb cs", command_string
        checksum = 0
        session_id = self.__sesion_id
        reply_id = self.__reply_id
        response_size = 1024
        data = []
        start = 0
        cmd_response = self.__send_command(1503, command_string, checksum, session_id, reply_id, response_size)
        if not cmd_response.get('status'):
            raise ZKErrorResponse("Not supported")
        size = unpack('I', self.__data_recv[9:13])[0]  # extra info???
        #print "size fill be %i" % size
        remain = size % MAX_CHUNK
        packets = (size-remain) / MAX_CHUNK # should be size /16k
        for _wlk in range(packets):
            data.append(self.__read_chunk(start,MAX_CHUNK))
            start += MAX_CHUNK
        if remain:
            data.append(self.__read_chunk(start, remain))
            start += remain # Debug
        self.free_data()
        #print "_read w/chunk %i bytes" % start
        return ''.join(data), start

    def get_attendance(self):
        """ return attendance record """
        attendances = []
        attendance_data, size = self.read_with_buffer(const.CMD_ATTLOG_RRQ)
        if size < 4:
            print "WRN: no attendance data" # debug
            return []
        attendance_data = attendance_data[4:] #total size not used
        if self.__firmware == 6:
            while len(attendance_data) >= 8:
                uid, status, timestamp = unpack('HH4s', attendance_data.ljust(8)[:8])
                user_id = str(uid) #TODO revisar posibles valores cruzar con userdata
                timestamp = self.__decode_time(timestamp)
                attendance = Attendance(uid, user_id, timestamp, status)
                attendances.append(attendance)
                attendance_data = attendance_data[8:]
        else:
            while len(attendance_data) >= 40:
                uid, user_id, sparator, timestamp, status, space = unpack('H24sc4sc8s', attendance_data.ljust(40)[:40])
                user_id = user_id.split('\x00')[0]
                timestamp = self.__decode_time(timestamp)
                status = int(status.encode("hex"), 16)

                attendance = Attendance(uid, user_id, timestamp, status)
                attendances.append(attendance)
                attendance_data = attendance_data[40:]
        return attendances
    def _get_attendance(self):
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
                pac = 1
                while True: #limitado por respuesta no por tamaño
                    data_recv = self.__sock.recv(1032)
                    response = unpack('HHHH', data_recv[:8])[0]
                    #print "# %s packet response is: %s" % (pac, response)
                    if response == const.CMD_DATA:
                        pac += 1
                        attendance_data.append(data_recv[8:]) #header turncated
                        bytes -= 1024
                    elif response == const.CMD_ACK_OK:
                        break #without problem.
                    else:
                        #truncado! continuar?
                        #print "broken!"
                        break
                    #print "still needs %s" % bytes
                if response == const.CMD_ACK_OK:
                    if attendance_data:
                        attendance_data = ''.join(attendance_data)
                        attendance_data = attendance_data[4:]
                        if self.__firmware == 6:
                            while len(attendance_data) >= 8:
                                uid, status, timestamp = unpack('HH4s', attendance_data.ljust(8)[:8])
                                user_id = str(uid) #TODO revisar posibles valores cruzar con userdata
                                timestamp = self.__decode_time(timestamp)
                                attendance = Attendance(uid, user_id, timestamp, status)
                                attendances.append(attendance)
                                attendance_data = attendance_data[8:]
                        else:
                            while len(attendance_data) >= 40:
                                uid, user_id, sparator, timestamp, status, space = unpack('H24sc4sc8s', attendance_data.ljust(40)[:40])
                                user_id = user_id.split('\x00')[0]
                                timestamp = self.__decode_time(timestamp)
                                status = int(status.encode("hex"), 16)

                                attendance = Attendance(uid, user_id, timestamp, status)
                                attendances.append(attendance)

                                attendance_data = attendance_data[40:]
                        self.free_data()
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
