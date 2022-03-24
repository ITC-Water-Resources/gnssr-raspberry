#!/usr/bin/env python

### import libraries ###
import requests
from datetime import date, timedelta
import xml.etree.ElementTree as ET
import re
import os
import glob

### get a list of already uploaded files ###
def getwebdavListing(davurl,auth,regexpr):
    xmlprop="""<propfind xmlns="DAV:">
      <prop>
        <getlastmodified xmlns="DAV:"/>
        <getcontentlength xmlns="DAV:"/>
        <executable xmlns="http://apache.org/dav/props/"/>
      </prop>
    </propfind>
    """
    xmlel=ET.fromstring(requests.request('PROPFIND',davurl,auth=auth,data=xmlprop).content)

    return  [os.path.basename(filename.text) for filename in xmlel.findall('.//{DAV:}href') if re.search(regexpr,filename.text)]

### Cridential to upload the files ###
from dotenv import load_dotenv
import os

load_dotenv()
webdav = os.getenv('webdav')
upluser = os.getenv('upluser')
uplpw = os.getenv('uplpw')
basicup = requests.auth.HTTPBasicAuth(upluser, uplpw)
#print (webdav)
#print (upluser)
#print(uplpw)

### Regular expression which fits a log file ###
relog='[0-9]{4}-[0-9]{2}-[0-9]{2}-gnssr2.gz'

### Get a listing for the remote directory ###
remotelogs=getwebdavListing(webdav,basicup,relog)
print(remotelogs)

### Also get a local directory listing ###
locallogs=[filename for filename in glob.glob('*') if re.search(relog,filename)]
print(locallogs)


### create a list of files which need to be uploaded ###
updatelogs=[filename for filename in locallogs if filename not in remotelogs]
print(updatelogs)

### Uploading files
for updatelog in updatelogs:
  print(updatelog)
  uplulr=webdav+"/"+updatelog
  with open (updatelog,'rb') as fid:
    requests.put(uplulr, dat=fid.read(), auth=basicup)
