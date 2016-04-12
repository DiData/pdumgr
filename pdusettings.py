#!/usr/bin/env python
import os
from requests import get as reqget, post as reqpost
from json import loads as jsonloads, dumps as jsondumps
from hashlib import sha1
from threading import Thread
from ftplib import FTP
from config import configSystem
import time
from shutil import copyfile

cfg = configSystem('config.cfg')

# The purpose of this script is very simple. We loop through a list of IPv6 auto configure addresses:
# - pull the config down via FTP
# - check for IPv4=disabled
# - replace with IPv4=enabled
# - upload config back up to FTP

# IPv6 or IPv4
ipv6 = False
# IPv6 Interface (only auto configuration required.)
interface = 'eth1'
# Put your IPv6 addresses in here (delimited by new line \n)
file = 'iplist.txt'

def scanner(data):
    print data
    ipaddr = data['ip_address']
    serial = data['serial_number']
    user = data['correct_user']
    pw = data['correct_pass']
    if len(user) == 0 or len(pw) == 0:
        print 'No user/pass for %s (s/n: %s)' % (ipaddr, serial)
        return False

    print 'Running FTP against: %s (s/n: %s)' % (ipaddr, serial)

    try:
        if ipv6 is True:
            ftp = FTP(ipaddr+'%'+interface, user, pw)
        else:
            ftp = FTP(ipaddr, user, pw)
    except:
        return False

    old_filename = 'config_old_'+serial+'.ini'
    new_filename = 'config_new_'+serial+'.ini'
    file = open(old_filename, 'wb')
    print 'Retrieving config.ini from %s' % ipaddr
    ftp.retrbinary('RETR config.ini', file.write)
    ftp.quit()

    file.close()
    copyfile(old_filename, new_filename)
    pduCfg = configSystem(new_filename)
    print pduCfg.getConfigValue('NetworkTCP/IP', 'IPv4')



    f1 = open(old_filename, 'r')
    f2 = open(new_filename, 'w')
    triggered = False
    for line in f1:
        if 'IPv4=disabled' in line:
            triggered = True
            f2.write(line.replace('disabled', 'enabled'))
        else:
            f2.write(line)
    f1.close()
    f2.close()

    print 'Triggered: %s, but skipping' % triggered
    return False


    if triggered is True:
        try:
            if ipv6 is True:
                ftp = FTP(ipaddr+'%'+interface, user, pw)
            else:
                ftp = FTP(ipaddr, user, pw)
        except:
            return False
        print 'Storing config.ini to %s' % ipaddr
        ftp.storbinary('STOR config.ini', open(new_filename, 'rb'))
        ftp.quit()

# Override
dccode = ''
#dccode = cfg.getConfigValue('pdu', 'dccode')
url = '%s/pdu/getPduData?dccode=%s' % (cfg.getConfigValue('pdu', 'api_base'), dccode)
r = reqget(url, headers={'SB-Auth-Key': cfg.getConfigValue('pdu', 'api_key')})
resp = r.json()
if 'data' not in resp:
    exit()

for data in resp['data']:
    if len(data['serial_number']) > 0:
        scanner(data)
#        t = Thread(target=scanner, args=(data,))
#        t.start()
#        time.sleep(.1)
