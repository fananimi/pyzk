from zk import ZK

IP = "192.168.66.114"
PORT = 4370
PASS = 50500   # حطي الكوم باسورد اللي اشتغل معاك

zk = ZK(IP, port=PORT, timeout=10, password=PASS)

conn = None
try:
    conn = zk.connect()
    print("✅ Connected")

    conn.disable_device()

    print("Time:", conn.get_time())
    print("Firmware:", conn.get_firmware_version())
    print("Platform:", conn.get_platform())
    print("Serial:", conn.get_serialnumber())

    conn.enable_device()

except Exception as e:
    print("❌ Error:", e)

finally:
    if conn:
        conn.disconnect()
