from zk import ZK

IP="192.168.66.114"; PORT=4370; PASS=50500
zk = ZK(IP, port=PORT, timeout=30, password=PASS)

conn=None
try:
    conn=zk.connect()
    conn.disable_device()

    logs = conn.get_attendance()
    print("Total logs:", len(logs))
    for a in logs[:50]:
        print(a.user_id, a.timestamp, a.status, a.verify)

    conn.enable_device()
except Exception as e:
    print("Error:", e)
finally:
    if conn: conn.disconnect()
