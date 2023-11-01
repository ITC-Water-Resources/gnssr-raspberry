"""
This file contains functionality to handle gnss-r configuration settings
Author: Roelof Rietbroek
"""

import os
import yaml
from datetime import datetime,date
import re
import asyncio
import gzip
import serial
from io import BytesIO
import aiohttp
import xml.etree.ElementTree as ET

NMEAsimbuf=BytesIO(b"""$GNVTG,337.73,T,,M,0.26,N,0.48,K,D*2D
$GNRMC,000000.000,A,5215.0780,N,00541.4066,E,0.26,337.73,071022,,,D*7C
$GNVTG,337.73,T,,M,0.26,N,0.48,K,D*2D
$GNGGA,000001.000,5215.0780,N,00541.4065,E,2,18,0.61,46.2,M,47.1,M,,*47
$GPGSA,A,3,05,18,31,12,02,26,11,04,25,16,29,20,0.87,0.61,0.63*09
$GLGSA,A,3,84,85,68,75,67,,,,,,,,0.87,0.61,0.63*1F
$GNRMC,000001.000,A,5215.0780,N,00541.4065,E,0.58,337.73,071022,,,D*77
$GNVTG,337.73,T,,M,0.58,N,1.07,K,D*2E
$GNGGA,000002.000,5215.0780,N,00541.4066,E,2,18,0.61,46.5,M,47.1,M,,*40
$GPGSA,A,3,05,18,31,12,02,26,11,04,25,16,29,20,0.87,0.61,0.63*09
$GLGSA,A,3,84,85,68,75,67,,,,,,,,0.87,0.61,0.63*1F
$GNRMC,000000.000,A,5215.0762,N,00541.4059,E,0.31,191.33,081022,,,D*7F
$GNVTG,191.33,T,,M,0.31,N,0.57,K,D*2F
$GNGGA,000001.000,5215.0762,N,00541.4059,E,2,18,0.56,59.4,M,47.1,M,,*48
$GPGSA,A,3,02,12,26,31,29,16,05,20,18,11,22,04,0.86,0.56,0.65*0D
$GLGSA,A,3,69,77,68,85,75,87,,,,,,,0.86,0.56,0.65*11
$GNRMC,000001.000,A,5215.0762,N,00541.4059,E,0.18,191.33,081022,,,D*75
$GNVTG,191.33,T,,M,0.18,N,0.34,K,D*21
$GNGGA,000002.000,5215.0762,N,00541.4059,E,2,19,0.55,59.4,M,47.1,M,,*49
$GPGSA,A,3,02,12,26,31,29,25,16,05,20,18,11,22,0.84,0.55,0.64*0E
$GLGSA,A,3,69,77,68,85,75,87,,,,,,,0.84,0.55,0.64*11
$GNRMC,000000.000,A,5215.0765,N,00541.4017,E,0.16,20.66,101022,,,D*45
$GNVTG,20.66,T,,M,0.16,N,0.29,K,D*18
$GNGGA,000001.000,5215.0765,N,00541.4018,E,2,17,0.68,51.5,M,47.1,M,,*41
$GPGSA,A,3,16,20,18,25,26,31,02,11,05,29,,,0.99,0.68,0.71*0B
$GLGSA,A,3,70,79,81,88,71,78,87,,,,,,0.99,0.68,0.71*10
$GNRMC,000001.000,A,5215.0765,N,00541.4018,E,0.20,20.66,101022,,,D*4E
$GNVTG,20.66,T,,M,0.20,N,0.38,K,D*1D
$GNGGA,000002.000,5215.0765,N,00541.4018,E,2,17,0.68,51.2,M,47.1,M,,*45
$GPGSA,A,3,16,20,18,25,26,31,02,11,05,29,,,0.99,0.68,0.71*0B
$GLGSA,A,3,70,79,81,88,71,78,87,,,,,,0.99,0.68,0.71*10
""")


class GNSSRconfig:
    def __init__(self,configfile=None,simulate=False,noupload=False):
        """Read the content of configuration file"""
        if not configfile:
            configfile=os.path.join(os.path.expanduser('~'),"nmeaconfig.yml")

        if not os.path.exists(configfile):
            raise RuntimeError(f"{configfile} does not exist")
        with open(configfile, "r") as ymlfile:
            self.cfg = yaml.safe_load(ymlfile)
        
        self.simulate=simulate
        self.noupload=noupload
        self.logfid=None
        if "serialsleep" in self.cfg:
            self.serialsleep=1e-3*self.cfg["serialsleep"]
        else:
            #default of 20 microseconds
            self.serialsleep=20e-3

        #possibly create the data directory if it doesn't exist yet
        if not os.path.exists(self.cfg['data_dir']):
            os.mkdir(self.cfg['data_dir'])
        #set the filename of the open logfile
        self.openLogFile=os.path.join(self.cfg['data_dir'],self.cfg['file_base']+".tmp")
        #default (will be updated from GNSS info)
        self.logdate=date.today()
        
        self.openSerial()
        self.setupWebdav()
     
    def setupWebdav(self):
        if "webdav" in self.cfg:
            self.webdav = self.cfg['webdav']['url']
            self.webdavauth=aiohttp.BasicAuth(login = self.cfg['webdav']['user'],
                                              password= self.cfg['webdav']['passw'])
        else:
            self.webdav=None

    def openSerial(self):
        """Open a serial port where we expect NMEA messages"""
        #note the timeout ensures that no data on the serial port will hang up the daemon (it needs to be large enough to get a fix though)
        if self.simulate:
            #fake a serial port with a bytesIO buffer
            self.serial= NMEAsimbuf

        else:
            #open the actual serial port
            self.serial = serial.Serial(self.cfg['device'],baudrate=self.cfg['baudrate'],timeout=120)

    async def rotateNMEAlog(self):
        """Asynchronuous functions which writes nmea messages to a log file and stops when a rotating criteria is obeyed"""
        prevdate=None
        #regular expression matching an RMC message
        rmcregex=re.compile(b'^\$G[NPL]RMC')
        #open logstream
        self.openLog()
        while self.isLogging:

            #Asynchronously wait for new serial data
            nmeamsg=await self.getnmea()
            if not nmeamsg.endswith(b"\n"):
                #no info -> try again later (or in the case of simulate data rewind the buffer
                if self.simulate:
                    self.serial.seek(0)
                    continue
                print("no data found on the serial port, retrying in one second")
                await asyncio.sleep(1)
                continue
            if rmcregex.match(nmeamsg):
                currentdate=datetime.strptime(nmeamsg.split(b",")[9].decode('utf-8'),"%d%m%y").date()
                if not prevdate:
                    prevdate=currentdate
                    self.logdate=currentdate

                if prevdate < currentdate:
                    break #will stop the loop at a date turnover

            self.writeToLog(nmeamsg)

        self.closeLog()
    
    def writeToLog(self,msg):
        """Possibly turn this into a non-blocking async function"""
        if self.logfid:
            self.logfid.write(msg)



    def openLog(self):
        print(f"Opening log {self.openLogFile}")
        if self.logfid:
            self.closeLog()
        self.logfid=gzip.open(self.openLogFile, 'wb')

    def closeLog(self):
        print(f"Closing open log {self.openLogFile}")

        if self.logfid:
            self.logfid.close()
            self.logfid=None 
        else:
            #nothing to do
            return

        #also move the file to a more suitable name
        logfilebase=os.path.join(self.cfg['data_dir'],f"{self.cfg['file_base']}_{self.logdate.isoformat()}")
        #make sure not to overwrite existing files
        c = 0
    
        # Check if there is already a file
        filenamegz=f"{logfilebase}_{c:02d}.gz"
        while os.path.exists(filenamegz) is True and c < 99:
            c+=1
        
            # Create file name
            filenamegz=f"{logfilebase}_{c:02d}.gz"


        print(f"Moving log to {filenamegz}")
        os.rename(self.openLogFile,filenamegz)

    async def getnmea(self):
        line=self.serial.readline()
        #sleeping xx microseconds allows other asynchronous work (e.g. file uploads) to be done while waiting for a new line on the serial input
        #note: we expect around ~10 nmea messages (lines) per seconds so we can wait and do other stuff in between
        await asyncio.sleep(self.serialsleep)
        return line

 
    async def getwebdavListing(self,regexlog):
        xmlprop="""<propfind xmlns="DAV:">
        <prop>
            <getlastmodified xmlns="DAV:"/>
            <getcontentlength xmlns="DAV:"/>
            <executable xmlns="http://apache.org/dav/props/"/>
        </prop>
        </propfind>
        """

        
        async with aiohttp.ClientSession(auth=self.webdavauth) as client:
            response= await client.request('PROPFIND',self.webdav,data=xmlprop)
            xmlbytes=await response.content.read() 
        xmlel=ET.fromstring(xmlbytes)
        
        return  [os.path.basename(filename.text) for filename in xmlel.findall('.//{DAV:}href') if regexlog.search(filename.text)]


    async def uploadLogWebdav(self,filename):
        """Upload a file to a  webdav folder"""
        
        uploadurl=self.webdav+"/"+os.path.basename(filename)
        async with aiohttp.ClientSession(auth=self.webdavauth) as client:
            with open (filename,'rb') as fid:
                print(f"Uploading {filename}")
                await client.put(uploadurl,data=fid.read())
    

    async def uploadLogs(self):
        """Asynchronuously upload logs to a webdav directory"""
        if not self.webdav or self.noupload:
            #no upload locations specified or upload is disabled 
            print("No upload location specified or disabled, cancelled upload")
            return

        regexlog=re.compile(f"{self.cfg['file_base']}_.+[0-9]{{2}}.gz")
        remotelogs=await self.getwebdavListing(regexlog)
        
        #get a local list with files which potentially need to be uploaded

        locallogs=[filename for filename in os.listdir(self.cfg['data_dir']) if regexlog.search(filename)]


        uploadlogs=[os.path.join(self.cfg['data_dir'],filename) for filename in locallogs if filename not in remotelogs]
        for logf in uploadlogs:
            await self.uploadLogWebdav(logf)

    
    async def startLoggingDaemon(self):
        self.isLogging=True
        while self.isLogging:
            synctask=asyncio.create_task(self.uploadLogs())
            await self.rotateNMEAlog()
            #wait for synctask to finish with timeout as a backup 
            # It should have been finished, and if not it should be cancelled 
            try:
                await asyncio.wait_for(synctask, timeout=60)
            except asyncio.TimeoutError:
                pass

    def stopLoggingDaemon(self,*args):
        """Gracefully stop logging (closes logging file)"""
        self.isLogging=False

