from zk import ZK

zk = ZK('192.168.66.114', port=4370, timeout=5, password=50500)

try:
    conn = zk.connect()
    print("Connected Successfully!")

    conn.disable_device()

    print("Device Time:", conn.get_time())
    print("Firmware:", conn.get_firmware_version())
    print("Platform:", conn.get_platform())

    conn.enable_device()
    conn.disconnect()

except Exception as e:
    print("Error:", e)
