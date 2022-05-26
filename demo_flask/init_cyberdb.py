import time
import cyberdb

db = cyberdb.Server()
# The data is persistent, the backup file is data.cdb, and the backup cycle is every 900 seconds.
db.set_backup('data.cdb', cycle=900)
# Set the TCP address, port number, and password.
# The start method will not block the operation. If you want the operation to block, please use the run method instead of start, and the parameters remain unchanged.
db.start(host='127.0.0.1', port=9980, password='123456')

while True:
    time.sleep(10000)
    print("")