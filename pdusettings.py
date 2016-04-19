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
from subprocess import call as proccall
import linecache
import fileinput

cfg = configSystem('config.cfg')

# Override
#dccode = ''
dccode = cfg.getConfigValue('pdu', 'dccode')

def wrf(b, file):
    if 'C for Celsius' not in b:
        file.write(b)


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
    ftp.retrbinary('RETR config.ini', lambda b: wrf(b, file))
    ftp.quit()

    file.close()

    # Detect version of NMC
    pduVer = linecache.getline(old_filename, 3)

    print pduVer

    pduCfg = configSystem(old_filename)

    triggered = False

    currentSnmpName = None
    currentSnmpContact = None
    currentSnmpLocation = None

    if 'RPDU 2g' in pduVer:
        currentTelnetMode = pduCfg.getConfigValue('NetworkTelnet', 'Access')
        if currentTelnetMode is not None and currentTelnetMode != 'disabled':
            pduCfg.setConfigValue('NetworkTelnet', 'Access', 'disabled')
            triggered = True

        currentSSHMode = pduCfg.getConfigValue('NetworkTelnet', 'ProtocolMode')
        if currentSSHMode is not None and currentSSHMode != 'enabled':
            pduCfg.setConfigValue('NetworkTelnet', 'ProtocolMode', 'enabled')
            triggered = True

        if 'hostname' in data and len(data['hostname']) > 0:
            currentSnmpName = pduCfg.getConfigValue('Device', 'NAME_A')
            newSnmpName = data['hostname']
            if currentSnmpName is not None and currentSnmpName != newSnmpName:
                pduCfg.setConfigValue('Device', 'NAME_A', newSnmpName)
                triggered = True

        currentSnmpContact = pduCfg.getConfigValue('Device', 'CONTACT_A')
        newSnmpContact = 'Infrastructure Team'
        if currentSnmpContact is not None and currentSnmpContact != newSnmpContact:
            pduCfg.setConfigValue('Device', 'CONTACT_A', newSnmpContact)
            triggered = True

        if 'loc' in data and len(data['loc']) > 0:
            currentSnmpLocation = pduCfg.getConfigValue('Device', 'LOCATION_A')
            newSnmpLocation = data['loc']
            if currentSnmpLocation is not None and currentSnmpLocation != newSnmpLocation:
                pduCfg.setConfigValue('Device', 'LOCATION_A', newSnmpLocation)
                triggered = True

    elif 'Rack PDU' in pduVer:
        currentTelnetMode = pduCfg.getConfigValue('NetworkTelnet', 'Telnet')
        if currentTelnetMode is not None and currentTelnetMode != 'disabled':
            pduCfg.setConfigValue('NetworkTelnet', 'Telnet', 'disabled')
            triggered = True

        currentSSHMode = pduCfg.getConfigValue('NetworkTelnet', 'SSH')
        if currentSSHMode is not None and currentSSHMode2 != 'enabled':
            pduCfg.setConfigValue('NetworkTelnet', 'SSH', 'enabled')
            triggered = True

        if 'hostname' in data and len(data['hostname']) > 0:
            currentSnmpName = pduCfg.getConfigValue('SystemID', 'Name')
            newSnmpName = data['hostname']
            if currentSnmpName is not None and currentSnmpName != newSnmpName:
                pduCfg.setConfigValue('SystemID', 'Name', newSnmpName)
                triggered = True

        currentSnmpContact = pduCfg.getConfigValue('SystemID', 'Contact')
        newSnmpContact = 'Infrastructure Team'
        if currentSnmpContact is not None and currentSnmpContact != newSnmpContact:
            pduCfg.setConfigValue('SystemID', 'Contact', newSnmpContact)
            triggered = True

        if 'loc' in data and len(data['loc']) > 0:
            currentSnmpLocation = pduCfg.getConfigValue('SystemID', 'Location')
            newSnmpLocation = data['loc']
            if currentSnmpLocation is not None and currentSnmpLocation != newSnmpLocation:
                pduCfg.setConfigValue('SystemID', 'Location', newSnmpLocation)
                triggered = True
    elif 'Automatic Transfer Switch' in pduVer:
        print 'Manually set up SNMP on: %s (s/n: %s)' % (ipaddr, serial)


    if 'hostname' in data and len(data['hostname']) > 0:
        currentHostname = pduCfg.getConfigValue('NetworkTCP/IP', 'HostName')
        newHostname = data['hostname']
        if currentHostname is not None and currentHostname != newHostname:
            pduCfg.setConfigValue('NetworkTCP/IP', 'HostName', newHostname)
            triggered = True

    currentDomain = pduCfg.getConfigValue('NetworkTCP/IP', 'DomainName')
    newDomain = 'infra-pdu.didata'
    if currentDomain is not None and currentDomain != newDomain:
        pduCfg.setConfigValue('NetworkTCP/IP', 'DomainName', newDomain)
        triggered = True

    print 'Current hostname: %s domain: %s' % (currentHostname, currentDomain)


    print 'Current snmpname: %s snmpcontact: %s snmplocation: %s' % (currentSnmpName, currentSnmpContact, currentSnmpLocation)

    if triggered is True:
        pduCfg.writeConfig(new_filename)
        proccall(['unix2dos', new_filename])
        try:
            if ipv6 is True:
                ftp = FTP(ipaddr+'%'+interface, user, pw)
            else:
                ftp = FTP(ipaddr, user, pw)
        except:
            print 'Exception while trying to connect to ip: %s u: %s p: %s' % (ipaddr, user, pw)
            return False
        print 'Storing config.ini to %s' % ipaddr
        try:
            ftp.storbinary('STOR config.ini', open(new_filename, 'rb'))
            ftp.quit()
        except:
            print 'Exception while trying to store config %s on %s' % (new_filename, ipaddr)
            return False

url = '%s/pdu/getPduData?dccode=%s' % (cfg.getConfigValue('pdu', 'api_base'), dccode)
r = reqget(url, headers={'SB-Auth-Key': cfg.getConfigValue('pdu', 'api_key')})
resp = r.json()
if 'data' not in resp:
    exit()

for data in resp['data']:
    if len(data['serial_number']) > 0:
#        scanner(data)
#        exit()
        t = Thread(target=scanner, args=(data,))
        t.start()
        time.sleep(.1)
