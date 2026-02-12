from zk import ZK

IP="192.168.66.114"; PORT=4370; PASS=50500
zk = ZK(IP, port=PORT, timeout=15, password=PASS)

conn=None
try:
    conn=zk.connect()
    conn.disable_device()

    users = conn.get_users()
    print("Total users:", len(users))
    for u in users[:20]:
        print(u.uid, u.user_id, u.name)

    conn.enable_device()
except Exception as e:
    print("Error:", e)
finally:
    if conn: conn.disconnect()
