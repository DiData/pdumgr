#!/usr/bin/env python
import os
from requests import get as reqget, post as reqpost, session as reqsession
from json import loads as jsonloads, dumps as jsondumps
from hashlib import sha1
from threading import Thread
from ftplib import FTP
from config import configSystem
import time
from shutil import copyfile
from regex import search as regsearch

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
    ipaddr = data['ip_address']
    serial = data['serial_number']
    user = data['correct_user']
    pw = data['correct_pass']

    # DO NOT RUN THIS AGAINST PDUs with STATIC IPS!!!!
    if ipaddr[:7] != "100.64.":
        return False

    if len(user) == 0 or len(pw) == 0:
        print 'No user/pass for %s (s/n: %s)' % (ipaddr, serial)
        return False

    print 'Running FTP_MOD against: %s (s/n: %s)' % (ipaddr, serial)

    defaultCookies = {'C0': 'apc'}

    sessionToken = ''
    appPrefix = ''
    pdusess = reqsession()

    login = {
        'login_username': user,
        'login_password': pw,
        'submit': 'Log On',
    }
    print 'Performing action: %s (s/n: %s): LOGIN1' % (ipaddr, serial)
    postres = pdusess.post('http://%s/Forms/login1' % ipaddr, data=login, allow_redirects=True)
    output = postres.text
    url = postres.url
    m = regsearch(r'%s\/(.*?)\/(.*?)\/' % ipaddr, url)
    if m:
        appPrefix = m.group(1)
        sessionToken = m.group(2)
        print 'Logged On: appPrefix: %s sessionToken: %s' % (appPrefix, sessionToken)
    else:
        print url
        return False

#    print 'Performing action: %s (s/n: %s): GENRESET1 {TCPIP}' % (ipaddr, serial)
#    tmpdata = { 'resetSelect': 'ResetExceptTCPIP', 'resetOnlyOptions': '?1', 'submit': 'Apply' }
#    resetres = pdusess.post('http://%s/%s/%s/Forms/genreset1' % (ipaddr, appPrefix, sessionToken), data=tmpdata)

#    print 'Performing action: %s (s/n: %s): RSTCNFRM1 {TCPIP}' % (ipaddr, serial)
#    tmpdata = { 'submit': 'Apply' }
#    resetres = pdusess.post('http://%s/%s/%s/Forms/rstcnfrm1' % (ipaddr, appPrefix, sessionToken), data=tmpdata)

    print 'Performing action: %s (s/n: %s): GENRESET1 {REBOOT}' % (ipaddr, serial)
    tmpdata = { 'resetSelect': 'Reboot', 'submit': 'Apply' }
    resetres = pdusess.post('http://%s/%s/%s/Forms/genreset1' % (ipaddr, appPrefix, sessionToken), data=tmpdata)

    print 'Performing action: %s (s/n: %s): RSTCNFRM1 {REBOOT}' % (ipaddr, serial)
    tmpdata = { 'submit': 'Apply' }
    resetres = pdusess.post('http://%s/%s/%s/Forms/rstcnfrm1' % (ipaddr, appPrefix, sessionToken), data=tmpdata)

    print 'Performing action: %s (s/n: %s): LOGOUT' % (ipaddr, serial)
    pdusess.get('http://%s/%s/%s/logout.htm' % (ipaddr, appPrefix, sessionToken))



#dccode = ''
dccode = cfg.getConfigValue('pdu', 'dccode')
url = '%s/pdu/getPduData?dccode=%s' % (cfg.getConfigValue('pdu', 'api_base'), dccode)
r = reqget(url, headers={'SB-Auth-Key': cfg.getConfigValue('pdu', 'api_key')})
resp = r.json()
if 'data' not in resp:
    exit()

#data = { 'ip_address': '100.64.137.235', 'serial_number': 'FAKE', 'correct_user': 'apc', 'correct_pass': 'apc'}
#scanner(data)

for data in resp['data']:
    if len(data['serial_number']) > 0:
#        scanner(data)
        t = Thread(target=scanner, args=(data,))
        t.start()
        time.sleep(.1)
