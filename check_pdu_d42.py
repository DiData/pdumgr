#!/usr/bin/env python
from requests import get as reqget, post as reqpost
from json import loads as jsonloads, dumps as jsondumps
from config import configSystem
from threading import Thread
from res_d42 import D42
import time, sys, os

cfg = configSystem('config.cfg')

d42obj = D42(
    cfg.getConfigValue('device42', 'd42_api_base'),
    cfg.getConfigValue('device42', 'd42_user'),
    cfg.getConfigValue('device42', 'd42_pass')
)

#pdudata = d42obj.api_get('/pdus/')['pdus']

def scanner(indata):
    if 'serial_number' not in indata:
        return False

    serial = indata['serial_number']

    if 'd42_id' in indata:
        if indata['d42_id'] > 0:
            return True

    matched = False
    matchedObj = None
#    print 'Running D42 check against: %s' % (serial)
    respdata = d42obj.api_get('/devices/all/?limit=50&serial_no=%s' % serial)
    if respdata['total_count'] > 0 and len(respdata['Devices']) > 0:
        matched = True
        matchedObj = respdata['Devices'][0]

    if matched:
        print 'Found S/N in D42: %s' % serial
        data = {
            'd42_pdu_mapping_url': matchedObj['pdu_mapping_url'],
            'd42_id': matchedObj['device_id'],
            'd42_name': matchedObj['name'],
            'real_serial': serial
        }
        url = '%s/pdu/update' % cfg.getConfigValue('pdu', 'api_base')
        r = reqpost(url, headers={'SB-Auth-Key': cfg.getConfigValue('pdu', 'api_key')}, json=data)
        print r.json()
    else:
        print 'S/N not found in D42: %s' % serial




url = '%s/pdu/getPduData?dccode=%s&params=d42_id,serial_number,hostname,d42_name' % (cfg.getConfigValue('pdu', 'api_base'), cfg.getConfigValue('pdu', 'dccode'))
r = reqget(url, headers={'SB-Auth-Key': cfg.getConfigValue('pdu', 'api_key')})
resp = r.json()
if 'data' not in resp:
    exit()

for data in resp['data']:
    if len(data['serial_number']) > 0:
        scanner(data)
#    t = Thread(target=scanner, args=(data,))
#    t.start()
