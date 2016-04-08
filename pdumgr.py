#!/usr/bin/env python

from requests import get as reqget, post as reqpost
from json import loads as jsonloads, dumps as jsondumps
from snmp_helper import snmp_get_oid,snmp_extract
from regex import search as regsearch
from nmap import PortScanner
from config import configSystem
from threading import Thread

import os, sys, getopt, pwd

cfg = configSystem('config.cfg')

def probePdu(host=None, state=None, snmp_port=161, ro_community=None, rw_community=None, dccode=None, url=None):
    print 'host: %s state: %s' % (host, state)
    if state == 'closed':
        return False

    pdu = (host, ro_community, snmp_port)
    snmp_data = snmp_get_oid(pdu, oid='.1.3.6.1.2.1.1.1.0', display_errors=False)
    if snmp_data is None:
        return False

    output = snmp_extract(snmp_data)
    if output is None:
        return False

    data = {'ip_address': host, 'dccode': dccode}

    m = regsearch(r'SN.+([0-9A-Z]{12})', output)
    if m:
        data['real_serial'] = m.group(1)

    m = regsearch(r'MN:([0-9A-Z]+)', output)
    if m:
        data['real_model'] = m.group(1)

    m = regsearch(r'MB:([v0-9\.]+)', output)
    if m:
        data['mbver'] = m.group(1)

    m = regsearch(r'HR:([A-Z0-9]+)', output)
    if m:
        data['hwrev'] = m.group(1)

    m = regsearch(r'PF:([v0-9\.]+)', output)
    if m:
        data['apcver'] = m.group(1)

    m = regsearch(r'PN:(.*?)\.bin', output)
    if m:
        data['apcverfile'] = m.group(1)

    m = regsearch(r'AF1:([v0-9\.]+)', output)
    if m:
        data['appmodver'] = m.group(1)

    m = regsearch(r'AN1:(.*?)\.bin', output)
    if m:
        data['appmodverfile'] = m.group(1)

    r = reqpost(url, headers={'SB-Auth-Key': cfg.getConfigValue('pdu', 'api_key')}, json=data)
    print r.json()



def main(argv):

    iprange = None

    try:
        opts, args = getopt.gnu_getopt(argv,"i:",["iprange="])
    except getopt.GetoptError:
        print sys.argv[0]+' -i <iprange>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print sys.argv[0]+' -i <iprange>'
            sys.exit()
        elif opt in ("-i", "--iprange"):
            iprange = arg

    if iprange is None:
        print sys.argv[0]+' -i <iprange>'
        sys.exit()

    scan_port = int(cfg.getConfigValue('pdu', 'scan_port'))
    snmp_port = int(cfg.getConfigValue('pdu', 'snmp_port'))
    ro_community = cfg.getConfigValue('pdu', 'ro_community')
    rw_community = cfg.getConfigValue('pdu', 'rw_community')
    dccode = cfg.getConfigValue('pdu', 'dccode')
    url = '%s/pdu/update' % cfg.getConfigValue('pdu', 'api_base')

    nm = PortScanner()
    nm.scan(hosts=iprange, arguments='-n -p %s' % (scan_port))

    for host in nm.all_hosts():
        state = nm[host]['tcp'][scan_port]['state']
        t = Thread(target=probePdu, args=(host, state, snmp_port, ro_community, rw_community, dccode, url))
        t.start()

if __name__ == "__main__":
   main(sys.argv[1:])