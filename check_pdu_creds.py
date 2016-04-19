#!/usr/bin/env python
from requests import get as reqget, post as reqpost
from json import loads as jsonloads, dumps as jsondumps
from config import configSystem
from threading import Thread
from ftplib import FTP
import time, sys, os

cfg = configSystem('config.cfg')

# Override
#dccode = ''
dccode = cfg.getConfigValue('pdu', 'dccode')

# Check PDU credentials and update our DB with the correct credentials
# Why the hell are we using FTP? Well, mostly because our other methods seem to block IPs after too many failed logins
url = '%s/pdu/getCredsPerDC?dccode=%s' % (cfg.getConfigValue('pdu', 'api_base'), dccode)
r = reqget(url, headers={'SB-Auth-Key': cfg.getConfigValue('pdu', 'api_key')})
resp = r.json()
print resp

if 'credlist' not in resp:
    exit()
else:
    credentialList = resp['credlist']

def scanner(ipaddr):
    if ipaddr is None and len(ipaddr) > 0:
        return False

    print 'Running FTP against: %s' % (ipaddr)

    goodCredential = None

    for cred in credentialList:
        ftp = FTP(ipaddr)
        try:
            ftp.login(cred['user'], cred['pw'])
            ftp.quit()
            goodCredential = cred
            break
        except Exception as e:
            if ftp is not None:
                ftp.quit()
#            print str(e)
            continue

    if goodCredential is None:
        return False

    print 'Good credential for %s:' % ipaddr, goodCredential
    data = {
        'ip_address': ipaddr,
        'correct_user': goodCredential['user'],
        'correct_pass': goodCredential['pw'],
    }

    url = '%s/pdu/update' % cfg.getConfigValue('pdu', 'api_base')
    r = reqpost(url, headers={'SB-Auth-Key': cfg.getConfigValue('pdu', 'api_key')}, json=data)
    print r.json()


url = '%s/pdu/getPduData?dccode=%s' % (cfg.getConfigValue('pdu', 'api_base'), dccode)
r = reqget(url, headers={'SB-Auth-Key': cfg.getConfigValue('pdu', 'api_key')})
resp = r.json()
if 'data' not in resp:
    exit()

for data in resp['data']:
    if len(data['serial_number']) > 0:
        ipaddr = data['ip_address']
#        scanner(data['ip_address'])
        t = Thread(target=scanner, args=(ipaddr,))
        t.start()
