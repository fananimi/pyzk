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
-- to the DNS protocol. That's OK. The goal isn't to fully dissect DNS properly - Wireshark already has a good
-- DNS dissector built-in. We don't need another one. We also have other example Lua scripts, but I don't think
-- they do a good job of explaining things, and the nice thing about this one is getting capture files to
-- run it against is trivial. (plus I uploaded one)
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
----------------------------------------
local pf_command   = ProtoField.new   ("Command", "zk6.command", ftypes.UINT16, rcomands, base.DEC)
local pf_checksum  = ProtoField.new   ("CheckSum", "zk6.checksum", ftypes.UINT16, nil, base.HEX)
local pf_sesion_id = ProtoField.uint16("zk6.session_id", "ID session", base.HEX)
local pf_reply_id  = ProtoField.uint16("zk6.reply_id", "ID Reply")
local pf_data      = ProtoField.new   ("Data", "zk6.data", ftypes.BYTES, nil, base.DOT)
local pf_time      = ProtoField.new   ("Time", "zk6.time", ftypes.UINT32, nil)

----------------------------------------
-- this actually registers the ProtoFields above, into our new Protocol
-- in a real script I wouldn't do it this way; I'd build a table of fields programmatically
-- and then set dns.fields to it, so as to avoid forgetting a field
zk.fields = { pf_command, pf_checksum, pf_sesion_id, pf_reply_id, pf_data, pf_time}

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
local command_field       = Field.new("zk6.command")
local checksum_field      = Field.new("zk6.checksum")
local session_id_field     = Field.new("zk6.session_id")
local reply_id_field        = Field.new("zk6.reply_id")
local data_field        = Field.new("zk6.data")
local time_field        =Field.new("zk6.time")
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
function zk.dissector(tvbuf,pktinfo,root)
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
    if pktlen > ZK_HDR_LEN then
        remain = pktlen - ZK_HDR_LEN -- TODO: no funciona el prevCommand,
        if (prevCommand == 201) or (prevCommand == 202) then
            local ts = tvbuf:range(8,4):le_uint()
            tree:add_le(pf_time, tvbuf:range(8,4)) 
        else
            tree:add_le(pf_data, tvbuf:range(8,remain))
        end
    end
    dprint2("zk.dissector returning",pktlen)
    prevCommand = tvbuf:range(0,2):le_uint()
    -- tell wireshark how much of tvbuff we dissected
    return pktlen
end

----------------------------------------
-- we want to have our protocol dissection invoked for a specific UDP port,
-- so get the udp dissector table and add our protocol to it
DissectorTable.get("udp.port"):add(default_settings.port, zk)


-- We're done!
-- our protocol (Proto) gets automatically registered after this script finishes loading
----------------------------------------

