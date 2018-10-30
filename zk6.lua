----------------------------------------
-- script-name: zk6_udp_dissector.lua
--
-- author: Arturo Hernandez 
-- Copyright (c) 2018
-- This code is in the Public Domain, or the BSD (3 clause) license if Public Domain does not apply
-- in your country.
--
-- Version: 1.0
--
-- BACKGROUND:
-- based on the example dns_dissector.lua from Hadriel Kaplan
--
-- OVERVIEW:
-- This script creates an dissector for the UDP protocol on ZK products. 
--
-- HOW TO RUN THIS SCRIPT:
-- Wireshark and Tshark support multiple ways of loading Lua scripts: through a dofile() call in init.lua,
-- through the file being in either the global or personal plugins directories, or via the command line.
-- See the Wireshark USer's Guide chapter on Lua (http://www.wireshark.org/docs/wsug_html_chunked/wsluarm.html).
-- Once the script is loaded, it creates a new protocol named "MyDNS" (or "MYDNS" in some places).  If you have
-- a capture file with DNS packets in it, simply select one in the Packet List pane, right-click on it, and
-- select "Decode As ...", and then in the dialog box that shows up scroll down the list of protocols to one
-- called "MYDNS", select that and click the "ok" or "apply" button.  Voila`, you're now decoding DNS packets
-- using the simplistic dissector in this script.  Another way is to download the capture file made for
-- this script, and open that - since the DNS packets in it use UDP port 65333 (instead of the default 53),
-- and since the MyDNS protocol in this script has been set to automatically decode UDP port 65333, it will
-- automagically do it without doing "Decode As ...".
--
----------------------------------------
print("hello world!")
-- do not modify this table
local debug_level = {
    DISABLED = 0,
    LEVEL_1  = 1,
    LEVEL_2  = 2
}

-- set this DEBUG to debug_level.LEVEL_1 to enable printing debug_level info
-- set it to debug_level.LEVEL_2 to enable really verbose printing
-- note: this will be overridden by user's preference settings
local DEBUG = debug_level.LEVEL_1

local default_settings = {
    debug_level  = DEBUG,
    port         = 4370,
    heur_enabled = false,
}

-- for testing purposes, we want to be able to pass in changes to the defaults
-- from the command line; because you can't set lua preferences from the command
-- line using the '-o' switch (the preferences don't exist until this script is
-- loaded, so the command line thinks they're invalid preferences being set)
-- so we pass them in as command arguments insetad, and handle it here:
local args={...} -- get passed-in args
if args and #args > 0 then
    for _, arg in ipairs(args) do
        local name, value = arg:match("(.+)=(.+)")
        if name and value then
            if tonumber(value) then
                value = tonumber(value)
            elseif value == "true" or value == "TRUE" then
                value = true
            elseif value == "false" or value == "FALSE" then
                value = false
            elseif value == "DISABLED" then
                value = debug_level.DISABLED
            elseif value == "LEVEL_1" then
                value = debug_level.LEVEL_1
            elseif value == "LEVEL_2" then
                value = debug_level.LEVEL_2
            else
                error("invalid commandline argument value")
            end
        else
            error("invalid commandline argument syntax")
        end

        default_settings[name] = value
    end
end

local dprint = function() end
local dprint2 = function() end
local function reset_debug_level()
    if default_settings.debug_level > debug_level.DISABLED then
        dprint = function(...)
            print(table.concat({"Lua:", ...}," "))
        end

        if default_settings.debug_level > debug_level.LEVEL_1 then
            dprint2 = dprint
        end
    end
end
-- call it now
reset_debug_level()

dprint2("Wireshark version = ", get_version())
dprint2("Lua version = ", _VERSION)

----------------------------------------
-- Unfortunately, the older Wireshark/Tshark versions have bugs, and part of the point
-- of this script is to test those bugs are now fixed.  So we need to check the version
-- end error out if it's too old.
local major, minor, micro = get_version():match("(%d+)%.(%d+)%.(%d+)")
if major and tonumber(major) <= 1 and ((tonumber(minor) <= 10) or (tonumber(minor) == 11 and tonumber(micro) < 3)) then
        error(  "Sorry, but your Wireshark/Tshark version ("..get_version()..") is too old for this script!\n"..
                "This script needs Wireshark/Tshark version 1.11.3 or higher.\n" )
end

-- more sanity checking
-- verify we have the ProtoExpert class in wireshark, as that's the newest thing this file uses
assert(ProtoExpert.new, "Wireshark does not have the ProtoExpert class, so it's too old - get the latest 1.11.3 or higher")

----------------------------------------


----------------------------------------
-- creates a Proto object, but doesn't register it yet
local zk = Proto("zk6","ZK600 UDP Protocol")
local zk_tcp = Proto("zk8","ZK800 TCP Protocol")

local rfct = {
    [1] = "FCT_ATTLOG",
    [8] = "FCT_WORKCODE",
    [2] = "FCT_FINGERTMP",
    [4] = "FCT_OPLOG",
    [5] = "FCT_USER",
    [6] = "FCT_SMS",
    [7] = "FCT_UDATA"
}

local rcomands = {
    [7] = "CMD_DB_RRQ",
    [8] = "CMD_USER_WRQ",
    [9] = "CMD_USERTEMP_RRQ",
    [10] = "CMD_USERTEMP_WRQ",
    [11] = "CMD_OPTIONS_RRQ",
    [12] = "CMD_OPTIONS_WRQ",
    [13] = "CMD_ATTLOG_RRQ",
    [14] = "CMD_CLEAR_DATA",
    [15] = "CMD_CLEAR_ATTLOG",
    [18] = "CMD_DELETE_USER",
    [19] = "CMD_DELETE_USERTEMP",
    [20] = "CMD_CLEAR_ADMIN",
    [21] = "CMD_USERGRP_RRQ",
    [22] = "CMD_USERGRP_WRQ",
    [23] = "CMD_USERTZ_RRQ",
    [24] = "CMD_USERTZ_WRQ",
    [25] = "CMD_GRPTZ_RRQ",
    [26] = "CMD_GRPTZ_WRQ",
    [27] = "CMD_TZ_RRQ",
    [28] = "CMD_TZ_WRQ",
    [29] = "CMD_ULG_RRQ",
    [30] = "CMD_ULG_WRQ",
    [31] = "CMD_UNLOCK",
    [32] = "CMD_CLEAR_ACC",
    [33] = "CMD_CLEAR_OPLOG",
    [34] = "CMD_OPLOG_RRQ",
    [50] = "CMD_GET_FREE_SIZES",
    [57] = "CMD_ENABLE_CLOCK",
    [60] = "CMD_STARTVERIFY",
    [61] = "CMD_STARTENROLL",
    [62] = "CMD_CANCELCAPTURE",
    [64] = "CMD_STATE_RRQ",
    [66] = "CMD_WRITE_LCD",
    [67] = "CMD_CLEAR_LCD",
    [69] = "CMD_GET_PINWIDTH",
    [70] = "CMD_SMS_WRQ",
    [71] = "CMD_SMS_RRQ",
    [72] = "CMD_DELETE_SMS",
    [73] = "CMD_UDATA_WRQ",
    [74] = "CMD_DELETE_UDATA",
    [75] = "CMD_DOORSTATE_RRQ",
    [76] = "CMD_WRITE_MIFARE",
    [78] = "CMD_EMPTY_MIFARE",
    [88] = "_CMD_GET_USER_TEMPLATE",
    [201] = "CMD_GET_TIME",
    [202] = "CMD_SET_TIME",
    [500] = "CMD_REG_EVENT",
    [1000] = "CMD_CONNECT",
    [1001] = "CMD_EXIT",
    [1002] = "CMD_ENABLEDEVICE",
    [1003] = "CMD_DISABLEDEVICE",
    [1004] = "CMD_RESTART",
    [1005] = "CMD_POWEROFF",
    [1006] = "CMD_SLEEP",
    [1007] = "CMD_RESUME",
    [1009] = "CMD_CAPTUREFINGER",
    [1011] = "CMD_TEST_TEMP",
    [1012] = "CMD_CAPTUREIMAGE",
    [1013] = "CMD_REFRESHDATA",
    [1014] = "CMD_REFRESHOPTION",
    [1017] = "CMD_TESTVOICE",
    [1100] = "CMD_GET_VERSION",
    [1101] = "CMD_CHANGE_SPEED",
    [1102] = "CMD_AUTH",
    [1500] = "CMD_PREPARE_DATA",
    [1501] = "CMD_DATA",
    [1502] = "CMD_FREE_DATA",
    [1503] = "CMD_PREPARE_BUFFER",
    [1504] = "CMD_READ_BUFFER",
    [2000] = "CMD_ACK_OK",
    [2001] = "CMD_ACK_ERROR",
    [2002] = "CMD_ACK_DATA",
    [2003] = "CMD_ACK_RETRY",
    [2004] = "CMD_ACK_REPEAT",
    [2005] = "CMD_ACK_UNAUTH",
    [65535] = "CMD_ACK_UNKNOWN",
    [65533] = "CMD_ACK_ERROR_CMD",
    [65532] = "CMD_ACK_ERROR_INIT",
    [65531] = "CMD_ACK_ERROR_DATA"
}
local rmachines = {
    [20560] = "MACHINE_PREPARE_DATA_1",
    [32130] = "MACHINE_PREPARE_DATA_2"
}
----------------------------------------
local pf_machine1  = ProtoField.new   ("Machine Data 1", "zk8.machine1", ftypes.UINT16, rmachines, base.DEC)
local pf_machine2  = ProtoField.new   ("Machine Data 2", "zk8.machine2", ftypes.UINT16, rmachines, base.DEC)
local pf_length    = ProtoField.new   ("Length", "zk8.length", ftypes.UINT32, nil, base.DEC)

local pf_command   = ProtoField.new   ("Command", "zk6.command", ftypes.UINT16, rcomands, base.DEC)
local pf_checksum  = ProtoField.new   ("CheckSum", "zk6.checksum", ftypes.UINT16, nil, base.HEX)
local pf_sesion_id = ProtoField.uint16("zk6.session_id", "ID session", base.HEX)
local pf_reply_id  = ProtoField.uint16("zk6.reply_id", "ID Reply")
local pf_commkey   = ProtoField.new   ("Communication key", "zk6.commkey", ftypes.UINT32, nil, base.HEX)
local pf_data      = ProtoField.new   ("Data", "zk6.data", ftypes.BYTES, nil, base.DOT)
local pf_string    = ProtoField.new   ("Data", "zk6.string", ftypes.STRING)
local pf_time      = ProtoField.new   ("Time", "zk6.time", ftypes.UINT32, nil)
local pf_start     = ProtoField.new   ("Data offset", "zk6.start", ftypes.UINT32, nil)
local pf_size      = ProtoField.new   ("Data Size", "zk6.size", ftypes.UINT32, nil)
local pf_psize     = ProtoField.new   ("Packet Size", "zk6.psize", ftypes.UINT32, nil)
local pf_fsize0    = ProtoField.new   ("null #1", "zk6.fsize0", ftypes.UINT32, nil)
local pf_fsize1    = ProtoField.new   ("null #2", "zk6.fsize1", ftypes.UINT32, nil)
local pf_fsize2    = ProtoField.new   ("null #3", "zk6.fsize2", ftypes.UINT32, nil)
local pf_fsize3    = ProtoField.new   ("null #4", "zk6.fsize3", ftypes.UINT32, nil)
local pf_fsizeu    = ProtoField.new   ("users", "zk6.fsizeu", ftypes.UINT32, nil)
local pf_fsize4    = ProtoField.new   ("null #5", "zk6.fsize4", ftypes.UINT32, nil)
local pf_fsizef    = ProtoField.new   ("fingers", "zk6.fsizef", ftypes.UINT32, nil)
local pf_fsize5    = ProtoField.new   ("null #6", "zk6.fsize5", ftypes.UINT32, nil)
local pf_fsizer    = ProtoField.new   ("records", "zk6.fsizer", ftypes.UINT32, nil)
local pf_fsize6    = ProtoField.new   ("null #7", "zk6.fsize6", ftypes.UINT32, nil)
local pf_fsize7    = ProtoField.new   ("null 4096", "zk6.fsize7", ftypes.UINT32, nil)
local pf_fsize8    = ProtoField.new   ("null #8", "zk6.fsize8", ftypes.UINT32, nil)
local pf_fsizec    = ProtoField.new   ("cards", "zk6.fsizec", ftypes.UINT32, nil)
local pf_fsize9    = ProtoField.new   ("null #9", "zk6.fsize9", ftypes.UINT32, nil)
local pf_fsizefc   = ProtoField.new   ("finger capacity", "zk6.fsizefc", ftypes.UINT32, nil)
local pf_fsizeuc   = ProtoField.new   ("user capacity", "zk6.fsizeuc", ftypes.UINT32, nil)
local pf_fsizerc   = ProtoField.new   ("record capacity", "zk6.fsizerc", ftypes.UINT32, nil)
local pf_fsizefa   = ProtoField.new   ("finger available", "zk6.fsizefa", ftypes.UINT32, nil)
local pf_fsizeua   = ProtoField.new   ("user available", "zk6.fsizeua", ftypes.UINT32, nil)
local pf_fsizera   = ProtoField.new   ("record available", "zk6.fsizera", ftypes.UINT32, nil)
local pf_fsizeff   = ProtoField.new   ("face", "zk6.fsizerff", ftypes.UINT32, nil)
local pf_fsize10   = ProtoField.new   ("nul #10", "zk6.fsize10", ftypes.UINT32, nil)
local pf_fsizeffc  = ProtoField.new   ("face capacity", "zk6.fsizeffc", ftypes.UINT32, nil)
local pf_pbfill    = ProtoField.new   ("null 01", "zk6.pbfill", ftypes.UINT8, nil)
local pf_pbcmd     = ProtoField.new   ("command", "zk6.pbcmd", ftypes.UINT16, rcomands)
local pf_pbarg     = ProtoField.new   ("argument", "zk6.pbarg", ftypes.UINT64, rfct)
local pf_pbfill0   = ProtoField.new   ("null 0", "zk6.pbfill0", ftypes.UINT8, nil)
local pf_pbfree    = ProtoField.new   ("free space", "zk6.pbfree", ftypes.UINT32, nil)
local pf_uid       = ProtoField.new   ("User ID", "zk6.uid", ftypes.UINT16, nil)
----------------------------------------
-- this actually registers the ProtoFields above, into our new Protocol
-- in a real script I wouldn't do it this way; I'd build a table of fields programmatically
-- and then set dns.fields to it, so as to avoid forgetting a field
zk.fields = { pf_command, pf_checksum, pf_sesion_id, pf_reply_id, pf_commkey, pf_data, pf_string,
              pf_time, pf_start, pf_size, pf_psize, pf_fsize0, pf_fsize1, pf_fsize2, pf_fsize3,
              pf_fsizeu, pf_fsize4, pf_fsizef, pf_fsize5,pf_fsizer,pf_fsize6,pf_fsize7,
              pf_fsize8,pf_fsizec,pf_fsize9,pf_fsizefc,pf_fsizeuc,pf_fsizerc, pf_uid,
              pf_fsizefa,pf_fsizeua,pf_fsizera, pf_fsizeff, pf_fsize10, pf_fsizeffc, 
              pf_pbfill, pf_pbcmd, pf_pbarg, pf_pbfill0, pf_pbfree}

zk_tcp.fields = { pf_machine1, pf_machine2, pf_length }
----------------------------------------
-- we don't just want to display our protocol's fields, we want to access the value of some of them too!
-- There are several ways to do that.  One is to just parse the buffer contents in Lua code to find
-- the values.  But since ProtoFields actually do the parsing for us, and can be retrieved using Field
-- objects, it's kinda cool to do it that way. So let's create some Fields to extract the values.
-- The following creates the Field objects, but they're not 'registered' until after this script is loaded.
-- Also, these lines can't be before the 'dns.fields = ...' line above, because the Field.new() here is
-- referencing fields we're creating, and they're not "created" until that line above.
-- Furthermore, you cannot put these 'Field.new()' lines inside the dissector function.
-- Before Wireshark version 1.11, you couldn't even do this concept (of using fields you just created).
local machine1_field   = Field.new("zk8.machine1")
local machine2_field   = Field.new("zk8.machine2")
local length_field    = Field.new("zk8.length")
local command_field    = Field.new("zk6.command")
local checksum_field   = Field.new("zk6.checksum")
local session_id_field = Field.new("zk6.session_id")
local reply_id_field   = Field.new("zk6.reply_id")
local commkey_field    = Field.new("zk6.commkey")
local data_field       = Field.new("zk6.data")
local string_field     = Field.new("zk6.string")
local time_field       = Field.new("zk6.time")
local size_field       = Field.new("zk6.size")
local start_field       = Field.new("zk6.start")
local psize_field      = Field.new("zk6.psize")
local fsize0_field     = Field.new("zk6.fsize0")
local fsize1_field     = Field.new("zk6.fsize1")
local fsize2_field     = Field.new("zk6.fsize2")
local fsize3_field     = Field.new("zk6.fsize3")
local fsize4_field     = Field.new("zk6.fsize4")
local fsize5_field     = Field.new("zk6.fsize5")
local fsize6_field     = Field.new("zk6.fsize6")
local fsize7_field     = Field.new("zk6.fsize7")
local fsize8_field     = Field.new("zk6.fsize8")
local fsize9_field     = Field.new("zk6.fsize9")
local fsizef_field     = Field.new("zk6.fsizef")
local fsizeu_field     = Field.new("zk6.fsizeu")
local fsizer_field     = Field.new("zk6.fsizer")
local fsizec_field     = Field.new("zk6.fsizec")
local pbfill_field     = Field.new("zk6.pbfill")
local pbcmd_field      = Field.new("zk6.pbcmd")
local pbarg_field      = Field.new("zk6.pbarg")
local pbfill0_field    = Field.new("zk6.pbfill0")
local pbfree_field     = Field.new("zk6.pbfree")
local uid_field        = Field.new("zk6.uid")

-- here's a little helper function to access the response_field value later.
-- Like any Field retrieval, you can't retrieve a field's value until its value has been
-- set, which won't happen until we actually use our ProtoFields in TreeItem:add() calls.
-- So this isResponse() function can't be used until after the pf_flag_response ProtoField
-- has been used inside the dissector.
-- Note that calling the Field object returns a FieldInfo object, and calling that
-- returns the value of the field - in this case a boolean true/false, since we set the
-- "mydns.flags.response" ProtoField to ftype.BOOLEAN way earlier when we created the
-- pf_flag_response ProtoField.  Clear as mud?
--
-- A shorter version of this function would be:
-- local function isResponse() return response_field()() end
-- but I though the below is easier to understand.
local function isResponse()
    local response_fieldinfo = response_field()
    return response_fieldinfo()
end

--------------------------------------------------------------------------------
-- preferences handling stuff
--------------------------------------------------------------------------------

-- a "enum" table for our enum pref, as required by Pref.enum()
-- having the "index" number makes ZERO sense, and is completely illogical
-- but it's what the code has expected it to be for a long time. Ugh.
local debug_pref_enum = {
    { 1,  "Disabled", debug_level.DISABLED },
    { 2,  "Level 1",  debug_level.LEVEL_1  },
    { 3,  "Level 2",  debug_level.LEVEL_2  },
}

zk.prefs.debug = Pref.enum("Debug", default_settings.debug_level,
                            "The debug printing level", debug_pref_enum)

zk.prefs.port  = Pref.uint("Port number", default_settings.port,
                            "The UDP port number for MyDNS")

zk.prefs.heur  = Pref.bool("Heuristic enabled", default_settings.heur_enabled,
                            "Whether heuristic dissection is enabled or not")

----------------------------------------
-- a function for handling prefs being changed
function zk.prefs_changed()
    dprint2("prefs_changed called")

    default_settings.debug_level  = zk.prefs.debug
    reset_debug_level()

    default_settings.heur_enabled = zk.prefs.heur

    if default_settings.port ~= zk.prefs.port then
        -- remove old one, if not 0
        if default_settings.port ~= 0 then
            dprint2("removing ZK6 from port",default_settings.port)
            DissectorTable.get("udp.port"):remove(default_settings.port, zk)
        end
        -- set our new default
        default_settings.port = dns.prefs.port
        -- add new one, if not 0
        if default_settings.port ~= 0 then
            dprint2("adding ZK6 to port",default_settings.port)
            DissectorTable.get("udp.port"):add(default_settings.port, zk)
        end
    end

end

dprint2("ZK6 Prefs registered")


----------------------------------------
---- some constants for later use ----
-- the DNS header size
local ZK_HDR_LEN = 8

-- the smallest possible DNS query field size
-- has to be at least a label length octet, label character, label null terminator, 2-bytes type and 2-bytes class
local MIN_QUERY_LEN = 7

----------------------------------------
-- some forward "declarations" of helper functions we use in the dissector
-- I don't usually use this trick, but it'll help reading/grok'ing this script I think
-- if we don't focus on them.
local getQueryName

local prevCommand = 0

----------------------------------------
-- The following creates the callback function for the dissector.
-- It's the same as doing "dns.dissector = function (tvbuf,pkt,root)"
-- The 'tvbuf' is a Tvb object, 'pktinfo' is a Pinfo object, and 'root' is a TreeItem object.
-- Whenever Wireshark dissects a packet that our Proto is hooked into, it will call
-- this function and pass it these arguments for the packet it's dissecting.
function zk.dissector(tvbuf, pktinfo, root)
    dprint2("zk.dissector called")

    -- set the protocol column to show our protocol name
    pktinfo.cols.protocol:set("ZK6")

    -- We want to check that the packet size is rational during dissection, so let's get the length of the
    -- packet buffer (Tvb).
    -- Because DNS has no additional payload data other than itself, and it rides on UDP without padding,
    -- we can use tvb:len() or tvb:reported_len() here; but I prefer tvb:reported_length_remaining() as it's safer.
    local pktlen = tvbuf:reported_length_remaining()

    -- We start by adding our protocol to the dissection display tree.
    -- A call to tree:add() returns the child created, so we can add more "under" it using that return value.
    -- The second argument is how much of the buffer/packet this added tree item covers/represents - in this
    -- case (DNS protocol) that's the remainder of the packet.
    local tree = root:add(zk, tvbuf:range(0,pktlen))

    -- now let's check it's not too short
    if pktlen < ZK_HDR_LEN then
        -- since we're going to add this protocol to a specific UDP port, we're going to
        -- assume packets in this port are our protocol, so the packet being too short is an error
        -- the old way: tree:add_expert_info(PI_MALFORMED, PI_ERROR, "packet too short")
        -- the correct way now:
        tree:add_proto_expert_info(ef_too_short)
        dprint("packet length",pktlen,"too short")
        return
    end

    -- Now let's add our transaction id under our dns protocol tree we just created.
    -- The transaction id starts at offset 0, for 2 bytes length.
    tree:add_le(pf_command, tvbuf:range(0,2))
    tree:add_le(pf_checksum, tvbuf:range(2,2))
    tree:add_le(pf_sesion_id, tvbuf:range(4,2))
    tree:add_le(pf_reply_id, tvbuf:range(6,2))
    local command = tvbuf:range(0,2):le_uint()
    if rcomands[command] ~= nil then
        --pktinfo.cols.info:set(rcomands[command])
        pktinfo.cols.info = string.sub(rcomands[command], 5)
    else
        --pktinfo.cols.info:set("CMD:" .. tostring(command))
        pktinfo.cols.info = "CMD:" .. tostring(command)
    end
    if pktlen > ZK_HDR_LEN then
        remain = pktlen - ZK_HDR_LEN -- TODO: no funciona el prevCommand,
        if (command == 1102) then --CMD_AUTH
            tree:add_le(pf_commkey, tvbuf:range(8,4))
        elseif (command == 1500) then --CMD_PREPARE_DATA
            tree:add_le(pf_size, tvbuf:range(8,4))
            pktinfo.cols.info = tostring(pktinfo.cols.info) .. " - " .. tvbuf:range(8,4):le_uint() .. " Bytes"
            if remain > 8 then
                tree:add_le(pf_psize, tvbuf:range(12,4))
            end
        elseif (command == 12) or (command == 11) then --CMD_OPTIONS_RRQ CMD_OPTIONS_WRQ
            tree:add(pf_string, tvbuf:range(8,remain))
            pktinfo.cols.info = tostring(pktinfo.cols.info) .. " - " .. tvbuf:range(8,remain):string()
        elseif (command == 18) then -- CMD_DELETE_USER
            tree:add_le(pf_uid, tvbuf(8,2))
            pktinfo.cols.info = tostring(pktinfo.cols.info) .. " UID: " .. tvbuf:range(8,2):le_uint()
        elseif (command == 88) then -- CMD_get_user_Template
            tree:add_le(pf_uid, tvbuf(8,2))
            tree:add_le(pf_pbfill0, tvbuf(10,1))
            pktinfo.cols.info = tostring(pktinfo.cols.info) .. " UID: " .. tvbuf:range(8,2):le_uint()
        elseif (command == 1503) then -- CMD_PREPARE_BUFFER
            tree:add(pf_pbfill, tvbuf:range(8,1))
            tree:add_le(pf_pbcmd, tvbuf:range(9,2))
            tree:add_le(pf_pbarg, tvbuf:range(11,8))
            pktinfo.cols.info = tostring(pktinfo.cols.info) .. " - " .. rcomands[tvbuf:range(9,2):le_uint()]
        elseif (command == 1504) then --CMD_READ_BUFFER
            tree:add_le(pf_start, tvbuf:range(8,4))
            tree:add_le(pf_size, tvbuf:range(12,4))
            pktinfo.cols.info = tostring(pktinfo.cols.info) .. " [" .. tvbuf:range(8,4):le_uint() .. "] -> " .. tvbuf:range(12,4):le_uint()
        elseif (command == 1501) then --CMD_DATA
            pktinfo.cols.info = tostring(pktinfo.cols.info) .. " " .. (remain) .. " Bytes"
            tree:add(pf_string, tvbuf:range(8,remain))
        elseif (prevCommand == 1503) then -- CMD_PREPARE_BUFFER OK!
            tree:add_le(pf_pbfill0, tvbuf:range(8,1))
            tree:add_le(pf_size, tvbuf:range(9,4))
            tree:add_le(pf_psize, tvbuf:range(13,4))
            tree:add_le(pf_pbfree, tvbuf:range(17,4))
            pktinfo.cols.info = tostring(pktinfo.cols.info) .. " BUFFER [" .. tvbuf:range(9,4):le_uint() .. "] (" .. tvbuf:range(13,4):le_uint() .. ")"
        elseif (prevCommand == 12) or (prevCommand == 11) or (prevCommand == 1100) then --CMD_OPTIONS_RRQ CMD_OPTIONS_WRQ OK
            tree:add(pf_string, tvbuf:range(8,remain))
            pktinfo.cols.info = tostring(pktinfo.cols.info) .. " RESP " .. tvbuf:range(8,remain):string()
        elseif (prevCommand == 201) or (prevCommand == 202) then
            local ts = tvbuf:range(8,4):le_uint()
            tree:add_le(pf_time, tvbuf:range(8,4))
        elseif (prevCommand == 50) then
            tree:add_le(pf_fsize0, tvbuf:range(8,4))
            tree:add_le(pf_fsize1, tvbuf:range(12,4))
            tree:add_le(pf_fsize2, tvbuf:range(16,4))
            tree:add_le(pf_fsize3, tvbuf:range(20,4))
            tree:add_le(pf_fsizeu, tvbuf:range(24,4))
            tree:add_le(pf_fsize4, tvbuf:range(28,4))
            tree:add_le(pf_fsizef, tvbuf:range(32,4))
            tree:add_le(pf_fsize5, tvbuf:range(36,4))
            tree:add_le(pf_fsizer, tvbuf:range(40,4))
            tree:add_le(pf_fsize6, tvbuf:range(44,4))
            tree:add_le(pf_fsize7, tvbuf:range(48,4))
            tree:add_le(pf_fsize8, tvbuf:range(52,4))
            tree:add_le(pf_fsizec, tvbuf:range(56,4))
            tree:add_le(pf_fsize9, tvbuf:range(60,4))
            tree:add_le(pf_fsizefc, tvbuf:range(64,4))
            tree:add_le(pf_fsizeuc, tvbuf:range(68,4))
            tree:add_le(pf_fsizerc, tvbuf:range(72,4))
            tree:add_le(pf_fsizefa, tvbuf:range(76,4))
            tree:add_le(pf_fsizeua, tvbuf:range(80,4))
            tree:add_le(pf_fsizera, tvbuf:range(84,4))
            if remain > 80 then
            tree:add_le(pf_fsizeff, tvbuf:range(88,4))
            tree:add_le(pf_fsize10, tvbuf:range(92,4))
            tree:add_le(pf_fsizeffc, tvbuf:range(96,4))
            end
        else
            -- tree:add_le(pf_data, tvbuf:range(8,remain)) most time we need strings
            tree:add(pf_string, tvbuf:range(8,remain))
        end
    end
    dprint2("zk.dissector returning",pktlen)

    prevCommand = command
    -- tell wireshark how much of tvbuff we dissected
    return pktlen
end
----------------------------------------
-- we want to have our protocol dissection invoked for a specific UDP port,
-- so get the udp dissector table and add our protocol to it
DissectorTable.get("udp.port"):add(default_settings.port, zk)


function zk_tcp.dissector(tvbuf, pktinfo, root)
    dprint2("zk_tcp.dissector called")
    local pktlen = tvbuf:reported_length_remaining()

    -- We start by adding our protocol to the dissection display tree.
    -- A call to tree:add() returns the child created, so we can add more "under" it using that return value.
    -- The second argument is how much of the buffer/packet this added tree item covers/represents - in this
    -- case (DNS protocol) that's the remainder of the packet.
    local tree = root:add(zk_tcp, tvbuf:range(0,pktlen))

    -- now let's check it's not too short
    if pktlen < ZK_HDR_LEN then
        -- since we're going to add this protocol to a specific UDP port, we're going to
        -- assume packets in this port are our protocol, so the packet being too short is an error
        -- the old way: tree:add_expert_info(PI_MALFORMED, PI_ERROR, "packet too short")
        -- the correct way now:
        tree:add_proto_expert_info(ef_too_short)
        dprint("packet length",pktlen,"too short")
        return
    end
    -- tell wireshark how much of tvbuff we dissected
    dprint2("zk_tcp.dissector returning", pktlen)
    local machine1 = tvbuf:range(0,2):le_uint()
    local machine2 = tvbuf:range(2,2):le_uint()

    if (machine1 == 20560) and (machine2 == 32130) then
        local tcp_length = tvbuf:range(4,4):le_uint64()
        tree:add_le(pf_machine1, tvbuf:range(0,2))
        tree:add_le(pf_machine2, tvbuf:range(2,2))
        tree:add_le(pf_length, tvbuf:range(4,4))
        if pktlen > ZK_HDR_LEN then
            remain = pktlen - ZK_HDR_LEN
            -- zk_tree  = tree:add(zk, tvbuf:range(8, remain))
            zk.dissector(tvbuf:range(8,remain):tvb(), pktinfo, tree)
        end
        -- set the protocol column to show our protocol name
        pktinfo.cols.protocol:set("ZK8")
    else
        pktinfo.cols.protocol:set("ZK8")
        pktinfo.cols.info:set("--- data " .. pktlen .. " Bytes")
    end
    return pktlen
end


DissectorTable.get("tcp.port"):add(default_settings.port, zk_tcp)
-- We're done!
-- our protocol (Proto) gets automatically registered after this script finishes loading
----------------------------------------

