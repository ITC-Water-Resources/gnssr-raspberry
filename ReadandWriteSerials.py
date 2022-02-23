import serial
import gzip
import time

class File:
    def __init__(self):
        current_date = time.strftime(\"%Y-%m-%d\")
        self.old_date = current_date
        self.filenamegz = \"{}.gz\".format(current_date)
        self.fid = gzip.open(self.filenamegz,'wt')

    def write(self, message):
        current_date = time.strftime(\"%Y-%m-%d\")

        if not current_date == self.old_date:
            self.old_date = current_date
            self.fid.close()
            self.filenamegz = \"{}.gz\".format(current_date)
            self.fid = gzip.open(self.filenamegz,'wt')

        self.fid.write(message)

    def close(self):
        self.fid.close()

file = File()
ser = serial.Serial ('/dev/ttyAMA0', baudrate=9600)
while True:
    try:
        file.write(ser.readline())
    except KeyboardInterrupt:
        file.close()
        break
