## Capture with TSHARK

1. Install tshark

   ```sh
   sudo apt install tshark
   ```

2. List interfaces

   ```sh
   thshark -D
   ```

3. capture interface (from appropriated interface, and correct host)

   ```sh
   tshark -i eth0 -f "host 192.168.1.201" -F pcapng -w capture.pcapng -P
   ```

4. test with another terminal

5. end capture with Ctrl+C

6. compress and attach file to issue!

