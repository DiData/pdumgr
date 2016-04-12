#!/usr/bin/env python
import os
from hashlib import sha1
from threading import Thread
from ftplib import FTP
import time

# The purpose of this script is very simple. We loop through a list of IPv6 auto configure addresses:
# - pull the config down via FTP
# - check for IPv4=disabled
# - replace with IPv4=enabled
# - upload config back up to FTP

# IPv6 or IPv4
ipv6 = False
# IPv6 Interface (only auto configuration required.)
interface = 'eth1'
# Default APC PDU username
defaultUser = 'apc'
# Default APC PDU password
defaultPass = 'apc'
# Put your IPv6 addresses in here (delimited by new line \n)
file = 'iplist.txt'

def scanner(ipaddr, uniq, interface, user, pw):
    print 'Running FTP against: %s uniq: %s' % (ipaddr, uniq)

    try:
        if ipv6 is True:
            ftp = FTP(ipaddr+'%'+interface, user, pw)
        else:
            ftp = FTP(ipaddr, user, pw)
    except:
        return False

    old_filename = 'config_old_'+uniq+'.ini'
    new_filename = 'config_new_'+uniq+'.ini'
    file = open(old_filename, 'wb')
    print 'Retrieving config.ini from %s' % ipaddr
    ftp.retrbinary('RETR config.ini', file.write)
    ftp.quit()

    file.close()

    return True

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


content = None
with open(file, 'r') as f:
    content = f.read()

lines = []
if content is None:
    exit()
else:
    lines = content.splitlines()

for ipaddr in lines:
    sh = sha1(ipaddr)
    t = Thread(target=scanner, args=(ipaddr, sh.hexdigest(), interface, defaultUser, defaultPass))
    t.start()
    time.sleep(.5)
