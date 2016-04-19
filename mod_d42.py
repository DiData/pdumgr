#!/usr/bin/env python
from requests import get as reqget, post as reqpost
from json import loads as jsonloads, dumps as jsondumps
from config import configSystem
from threading import Thread
from res_d42 import D42
import time, sys, os

cfg = configSystem('config.cfg')

# Override
#dccode = ''
dccode = cfg.getConfigValue('pdu', 'dccode')

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
        if indata['d42_id'] == 0:
            return True

    updateData = {
#        'name': indata['d42_name'],
        'new_name': indata['hostname'],
        'asset_no': indata['asset_tag'],
        'device_id': indata['d42_id'],
        'serial_no': indata['serial_number'],
    }
    respdevdata = d42obj.api_put('/device/', updateData)
    print updateData
    print respdevdata

    updatePduData = {
        'pdu_id': indata['pdu_id'],
        'name': indata['hostname'],
        'asset_no': indata['asset_tag'],
    }
    resppdudata = d42obj.api_put('/pdus/', updatePduData)
    print updatePduData
    print resppdudata

    exit()

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
            'real_serial': serial,
        }
        url = '%s/pdu/update' % cfg.getConfigValue('pdu', 'api_base')
        r = reqpost(url, headers={'SB-Auth-Key': cfg.getConfigValue('pdu', 'api_key')}, json=data)
        try:
            print r.json()
        except ValueError:
            print r.text
    else:
        print 'S/N not found in D42: %s' % serial
        data = {
            'd42_pdu_mapping_url': '',
            'd42_id': '',
            'd42_name': '',
            'real_serial': serial,
        }
        url = '%s/pdu/update' % cfg.getConfigValue('pdu', 'api_base')
        r = reqpost(url, headers={'SB-Auth-Key': cfg.getConfigValue('pdu', 'api_key')}, json=data)
        try:
            print r.json()
        except ValueError:
            print r.text

    exit()

url = '%s/pdu/getPduData?dccode=%s&params=d42_id,serial_number,hostname,d42_name,pdu_id,pdu_name,asset_tag' % (cfg.getConfigValue('pdu', 'api_base'), dccode)
r = reqget(url, headers={'SB-Auth-Key': cfg.getConfigValue('pdu', 'api_key')})
resp = r.json()
if 'data' not in resp:
    exit()

for data in resp['data']:
    if len(data['serial_number']) > 0:
        scanner(data)
#        t = Thread(target=scanner, args=(data,))
#        t.start()
