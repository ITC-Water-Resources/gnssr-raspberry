#!/usr/bin/env python

import serial
import gzip
import re

class File:
    def __init__(self):
        self.current_date = None
        self.old_date = None
        self.buffer = []
        self.fid = None

    def ropen_file(self):
        '''This function rotates a file (if file descriptor is open) or only open a new 
        file descriptor is none is open '''
        if self.fid:
            self.fid.close()

        self.filenamegz = "{}-gnssr2.gz".format(self.current_date)
        self.fid = gzip.open(self.filenamegz, 'wt')
        self.old_date = self.current_date

    def write(self, message):
        ''' Adding received GPS message to the buffer '''
        self.buffer.append(message)

        ''' Looking for a new timestamp in GNRMC '''
        if re.match("\$GNRMC.\d{6}\,.", message):
            try:
                current_date = message.split(",")[9].strip()

                if re.match("\d{6}", current_date):
                    self.current_date = current_date
                    
            except:
                pass

        ''' Rotating and writing to a file if we know current date '''
        if self.current_date:
            ''' Open a new file descriptor or rotate if date has changed '''
            if not self.fid() or not self.current_date == self.old_date:
                self.ropen_file()

            ''' Popping buffer content to a file '''
            while self.buffer():
                self.fid.write(self.buffer.pop(0))

    def close(self):
        self.fid.close()

file=File()
ser = serial.Serial('/dev/ttyAMA0', baudrate=9600)
while True:
    try:
        file.write(ser.readline().strip())

    except KeyboardInterrupt:
        file.close()
        break
