# -*- coding: utf-8 -*-

USHRT_MAX = 65535

CMD_DB_RRQ          = 7     # Read in some kind of data from the machine
CMD_USER_WRQ        = 8     # Upload the user information (from PC to terminal).
CMD_USERTEMP_RRQ    = 9     # Read some fingerprint template or some kind of data entirely
CMD_USERTEMP_WRQ    = 10    # Upload some fingerprint template
CMD_OPTIONS_RRQ     = 11    # Read in the machine some configuration parameter
CMD_OPTIONS_WRQ     = 12    # Set machines configuration parameter
CMD_ATTLOG_RRQ      = 13    # Read all attendance record
CMD_CLEAR_DATA      = 14    # clear Data
CMD_CLEAR_ATTLOG    = 15    # Clear attendance records
CMD_DELETE_USER     = 18    # Delete some user
CMD_DELETE_USERTEMP = 19    # Delete some fingerprint template
CMD_CLEAR_ADMIN     = 20    # Cancel the manager
CMD_USERGRP_RRQ     = 21    # Read the user grouping
CMD_USERGRP_WRQ     = 22    # Set users grouping
CMD_USERTZ_RRQ      = 23    # Read the user Time Zone set
CMD_USERTZ_WRQ      = 24    # Write the user Time Zone set
CMD_GRPTZ_RRQ       = 25    # Read the group Time Zone set
CMD_GRPTZ_WRQ       = 26    # Write the group Time Zone set
CMD_TZ_RRQ          = 27    # Read Time Zone set
CMD_TZ_WRQ          = 28    # Write the Time Zone
CMD_ULG_RRQ         = 29    # Read unlocks combination
CMD_ULG_WRQ         = 30    # write unlocks combination
CMD_UNLOCK          = 31    # unlock
CMD_CLEAR_ACC       = 32    # Restores Access Control set to the default condition.
CMD_CLEAR_OPLOG     = 33    # Delete attendance machines all attendance record.
CMD_OPLOG_RRQ       = 34    # Read manages the record
CMD_GET_FREE_SIZES  = 50    # Obtain machines condition, like user recording number and so on
CMD_ENABLE_CLOCK    = 57    # Ensure the machine to be at the normal work condition
CMD_STARTVERIFY     = 60    # Ensure the machine to be at the authentication condition
CMD_STARTENROLL     = 61    # Start to enroll some user, ensure the machine to be at the registration user condition
CMD_CANCELCAPTURE   = 62    # Make the machine to be at the waiting order status, please refers to the CMD_STARTENROLL description.
CMD_STATE_RRQ       = 64    # Gain the machine the condition
CMD_WRITE_LCD       = 66    # Write LCD
CMD_CLEAR_LCD       = 67    # Clear the LCD captions (clear screen).
CMD_GET_PINWIDTH    = 69    # Obtain the length of user’s serial number
CMD_SMS_WRQ         = 70    # Upload the short message.
CMD_SMS_RRQ         = 71    # Download the short message
CMD_DELETE_SMS      = 72    # Delete the short message
CMD_UDATA_WRQ       = 73    # Set user’s short message
CMD_DELETE_UDATA    = 74    # Delete user’s short message
CMD_DOORSTATE_RRQ   = 75    # Obtain the door condition
CMD_WRITE_MIFARE    = 76    # Write the Mifare card
CMD_EMPTY_MIFARE    = 78    # Clear the Mifare card

CMD_GET_TIME        = 201   # Obtain the machine time
CMD_SET_TIME        = 202   # Set machines time
CMD_REG_EVENT       = 500   # Register the event

CMD_CONNECT         = 1000  # Connections requests
CMD_EXIT            = 1001  # Disconnection requests
CMD_ENABLEDEVICE    = 1002  # Ensure the machine to be at the normal work condition
CMD_DISABLEDEVICE   = 1003  # Make the machine to be at the shut-down condition, generally demonstrates ‘in the work ...’on LCD
CMD_RESTART         = 1004  # Restart the machine.
CMD_POWEROFF        = 1005  # Shut-down power source
CMD_SLEEP           = 1006  # Ensure the machine to be at the idle state.
CMD_RESUME          = 1007  # Awakens the sleep machine (temporarily not to support)
CMD_CAPTUREFINGER   = 1009  # Captures fingerprints picture
CMD_TEST_TEMP       = 1011  # Test some fingerprint exists or does not
CMD_CAPTUREIMAGE    = 1012  # Capture the entire image
CMD_REFRESHDATA     = 1013  # Refresh the machine interior data
CMD_REFRESHOPTION   = 1014  # Refresh the configuration parameter
CMD_TESTVOICE       = 1017  # Play voice
CMD_GET_VERSION     = 1100  # Obtain the firmware edition
CMD_CHANGE_SPEED    = 1101  # Change transmission speed
CMD_AUTH            = 1102  # Connections authorizations
CMD_PREPARE_DATA    = 1500  # Prepares to transmit the data
CMD_DATA            = 1501  # Transmit a data packet
CMD_FREE_DATA       = 1502  # Clear machines opened buffer

CMD_ACK_OK          = 2000  # Return value for order perform successfully
CMD_ACK_ERROR       = 2001  # Return value for order perform failed
CMD_ACK_DATA        = 2002  # Return data
CMD_ACK_RETRY       = 2003  # * Regstered event occorred */
CMD_ACK_REPEAT      = 2004  # Not available
CMD_ACK_UNAUTH      = 2005  # Connection unauthorized

CMD_ACK_UNKNOWN     = 0xffff# Unkown order
CMD_ACK_ERROR_CMD   = 0xfffd# Order false
CMD_ACK_ERROR_INIT  = 0xfffc#/* Not Initializated */
CMD_ACK_ERROR_DATA  = 0xfffb# Not available

EF_ATTLOG           = 1     # Be real-time to verify successfully
EF_FINGER           = (1<<1)# be real–time to press fingerprint (be real time to return data type sign)
EF_ENROLLUSER       = (1<<2)# Be real-time to enroll user
EF_ENROLLFINGER     = (1<<3)# be real-time to enroll fingerprint
EF_BUTTON           = (1<<4)# be real-time to press button
EF_UNLOCK           = (1<<5)# be real-time to unlock
EF_VERIFY           = (1<<7)# be real-time to verify fingerprint
EF_FPFTR            = (1<<8)# be real-time capture fingerprint minutia
EF_ALARM            = (1<<9)# Alarm signal

USER_DEFAULT        = 0
USER_ENROLLER       = 2
USER_MANAGER        = 6
USER_ADMIN          = 14

FCT_ATTLOG          = 1
FCT_WORKCODE        = 8
FCT_FINGERTMP       = 2
FCT_OPLOG           = 4
FCT_USER            = 5
FCT_SMS             = 6
FCT_UDATA           = 7

MACHINE_PREPARE_DATA_1 = 20560 # 0x5050
MACHINE_PREPARE_DATA_2 = 32130 # 0x7282