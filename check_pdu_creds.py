#!/usr/bin/env python
from requests import get as reqget, post as reqpost
from json import loads as jsonloads, dumps as jsondumps
from config import configSystem
from threading import Thread
from ftplib import FTP
import time, sys, os

cfg = configSystem('config.cfg')

# Check PDU credentials and update our DB with the correct credentials
# Why the hell are we using FTP? Well, mostly because our other methods seem to block IPs after too many failed logins
url = '%s/pdu/getCredsPerDC?dccode=%s' % (cfg.getConfigValue('pdu', 'api_base'), cfg.getConfigValue('pdu', 'dccode'))
r = reqget(url, headers={'SB-Auth-Key': cfg.getConfigValue('pdu', 'api_key')})
resp = r.json()
if 'credlist' not in resp:
    exit()
else:
    credentialList = resp['credlist']

def scanner(ipaddr):
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

url = '%s/pdu/getPduIpList?dccode=%s' % (cfg.getConfigValue('pdu', 'api_base'), cfg.getConfigValue('pdu', 'dccode'))
r = reqget(url, headers={'SB-Auth-Key': cfg.getConfigValue('pdu', 'api_key')})
print r.json()
resp = r.json()
if 'iplist' not in resp:
    exit()

for ipaddr in resp['iplist']:
#    scanner(ipaddr)
    t = Thread(target=scanner, args=(ipaddr,))
    t.start()
