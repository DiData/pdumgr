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

class pduWeb:
    __sess = None
    __ipaddr = ''
    __user = ''
    __pw = ''
    __secure = False
    __defaultCookies = {'C0': 'apc'}
    __appPrefix = ''
    __sessionToken = ''
    __debug = False
    __lastRequest = None

    def __init__(self, ipaddr='', user='', pw='', debug=False):
        self.__sess = reqsession()
        self.__ipaddr = ipaddr
        self.__user = user
        self.__pw = pw
        self.__debug = debug

    def getUrlPrefix(self, noPrefix=False):
        if self.__secure:
            if noPrefix:
                return 'https://%s' % self.__ipaddr
            else:
                return 'https://%s/%s/%s' % (self.__ipaddr, self.__appPrefix, self.__sessionToken)
        else:
            if noPrefix:
                return 'http://%s' % self.__ipaddr
            else:
                return 'http://%s/%s/%s' % (self.__ipaddr, self.__appPrefix, self.__sessionToken)

    def login(self):
        loginParams = {
            'login_username': self.__user,
            'login_password': self.__pw,
            'submit': 'Log On',
        }

        loginUrl = '%s/Forms/login1' % self.getUrlPrefix(noPrefix=True)

        if self.__debug:
            print 'Sending login request to %s login Params: %s' % (loginUrl, loginParams)

        self.__lastRequest = self.__sess.post(loginUrl, data=loginParams)

        m = regsearch(r'%s\/(.*?)\/(.*?)\/' % self.__ipaddr, self.__lastRequest.url)
        if m:
            self.__appPrefix = m.group(1)
            self.__sessionToken = m.group(2)

            if self.__debug:
                print 'Logged On: appPrefix: %s sessionToken: %s' % (self.__appPrefix, self.__sessionToken)
            return True
        else:
            raise RuntimeError('Cannot login to pdu %s' % (self.__ipaddr))

    def logout(self):
        logoutUrl = '%s/logout.htm' % self.getUrlPrefix()

        if self.__debug:
            print 'Sending logout request to %s' % (logoutUrl)
        self.__lastRequest = self.__sess.get(logoutUrl)
        self.__appPrefix = ''
        self.__sessionToken = ''

    def reboot(self):
        rebootUrl = '%s/Forms/genreset1' % self.getUrlPrefix()

        tmpdataReboot = { 'resetSelect': 'Reboot', 'submit': 'Apply' }
        if self.__debug:
            print 'Sending reboot request to %s with data: %s' % (rebootUrl, tmpdataReboot)
        self.__lastRequest = self.__sess.post(rebootUrl, data=tmpdataReboot)

        rebootConfirmUrl = '%s/Forms/rstcnfrm1' % self.getUrlPrefix()

        tmpdataConfirm = { 'submit': 'Apply' }
        if self.__debug:
            print 'Sending reboot confirm to %s with data: %s' % (rebootConfirmUrl, tmpdataConfirm)
        self.__lastRequest = self.__sess.post(rebootConfirmUrl, data=tmpdataConfirm)


    def setDns(self, primaryDns='0.0.0.0', secondaryDns='0.0.0.0', dnshostname='noname', dnsdomainname='infra-pdu.didata', dnsdomainnamev6='infra-pdu-v6.didata'):
        requestUrl = '%s/Forms/dnscfg1' % self.getUrlPrefix()
        tmpDataDns = {
            'overridedns': 'on',
            'PrimaryDNSServer': primaryDns,
            'SecondaryDNSServer': secondaryDns,
            'DNSHostName': dnshostname,
            'DNSDomainName': dnsdomainname,
            'DNSDomainNameIPv6': dnsdomainnamev6,
            'submit': 'Apply',
        }
        if self.__debug:
            print 'Sending DNS request to %s with data: %s' % (requestUrl, tmpDataDns)
        self.__lastRequest = self.__sess.post(requestUrl, data=tmpDataDns)
        if self.__lastRequest.status_code == 404:
            print self.__lastRequest.status_code, self.__lastRequest.url
            requestUrl = '%s/Forms/dnsserv1' % self.getUrlPrefix()
            tmpDataDns = {
                'PrimaryDNSServer': primaryDns,
                'SecondaryDNSServer': secondaryDns,
                'submit': 'Apply',
            }
            if self.__debug:
                print 'Sending DNSserv (legacy) request to %s with data: %s' % (requestUrl, tmpDataDns)
            self.__lastRequest = self.__sess.post(requestUrl, data=tmpDataDns)
            if self.__lastRequest.status_code != 303:
                print self.__lastRequest.status_code, self.__lastRequest.url

            requestUrl = '%s/Forms/dnsname1' % self.getUrlPrefix()
            tmpDataDns = {
                'DNSHostName': dnshostname,
                'DNSDomainName': dnsdomainname,
                'submit': 'Apply',
            }
            if self.__debug:
                print 'Sending DNSname (legacy) request to %s with data: %s' % (requestUrl, tmpDataDns)
            self.__lastRequest = self.__sess.post(requestUrl, data=tmpDataDns)
            if self.__lastRequest.status_code != 303:
                print self.__lastRequest.status_code, self.__lastRequest.url


    def setSSH(self):
        requestUrl = '%s/Forms/console1' % self.getUrlPrefix()
        tmpDataSsh = {
            'consoleModeEnableDisable': 'sshv2',
            'ConsolePort': '23',
            'ConsoleSSHPort': '22',
            'sshAccess': 'on',
            'submit': 'Apply',
        }
        if self.__debug:
            print 'Sending SSH request to %s with data: %s' % (requestUrl, tmpDataSsh)
        self.__lastRequest = self.__sess.post(requestUrl, data=tmpDataSsh, allow_redirects=False)
        if self.__lastRequest.status_code != '200' and 'Location' in self.__lastRequest.headers:
            if 'sshcnfrm.htm' in self.__lastRequest.headers['Location']:
                requestUrl = '%s/Forms/sshcnfrm1' % self.getUrlPrefix()
                tmpDataSshAccept = {
                    'submit': 'Accept Terms',
                }
                if self.__debug:
                    print 'Sending SSH terms agreement to %s with data: %s' % (requestUrl, tmpDataSshAccept)
                self.__lastRequest = self.__sess.post(requestUrl, data=tmpDataSshAccept)
                if self.__lastRequest.status_code != 303:
                    print self.__lastRequest.status_code, self.__lastRequest.url

    def setNtp(self, primaryNtp='0.0.0.0', secondaryNtp='0.0.0.0', ntpUpdateFrequency='1', ntpUpdateNow='on', timezone='0d000000'):
        requestUrl = '%s/Forms/dateman1' % self.getUrlPrefix()
        tmpDataNtp = {
            'timeZone': timezone,
            'date_time_mode': 'Remove',
            'primaryNTPServer': primaryNtp,
            'secondaryNTPServer': secondaryNtp,
            'ntpUpdateFrequency': ntpUpdateFrequency,
            'ntpUpdateNow': ntpUpdateNow,
            'submit': 'Apply',
        }
        if self.__debug:
            print 'Sending NTP request to %s with data: %s' % (requestUrl, tmpDataNtp)
        self.__lastRequest = self.__sess.post(requestUrl, data=tmpDataNtp)


    def setIdentification(self, hostname='', contact='Infrastructure Team', location=''):
        requestUrl = '%s/genid.htm' % self.getUrlPrefix()
        self.__lastRequest = self.__sess.get(requestUrl)
        preData = self.__lastRequest.text

        tmpDataID = {
            'arak_sysName': hostname,
            'arak_sysContact': contact,
            'arak_sysLocation': location,
            'submit': 'Apply',
        }

        if 'arak_sysNameHostLink' in preData:
            tmpDataID['arak_sysNameHostLink'] = 'on'

        if 'arak_loginMessage' in preData:
            tmpDataID['arak_loginMessage'] = ''

        requestUrl = '%s/Forms/genid1' % self.getUrlPrefix()
        if self.__debug:
            print 'Sending Identification request to %s with data: %s' % (requestUrl, tmpDataID)
        self.__lastRequest = self.__sess.post(requestUrl, data=tmpDataID)
        if self.__lastRequest.status_code != 303:
            print self.__lastRequest.status_code, self.__lastRequest.url

    def resetTcpIpSettings(self):
        requestUrl = '%s/Forms/genreset1' % self.getUrlPrefix()
        tmpDataTcpIp = {
            'resetSelect': 'ResetExceptTCPIP',
            'resetOnlyOptions': '?1',
            'submit': 'Apply'
        }

        if self.__debug:
            print 'Sending TcpIp request to %s with data: %s' % (requestUrl, tmpDataTcpIp)
        self.__lastRequest = self.__sess.post(requestUrl, data=tmpDataTcpIp, allow_redirects=False)

        requestUrl = '%s/Forms/rstcnfrm1' % self.getUrlPrefix()
        tmpDataTcpIp2 = {
            'submit': 'Apply'
        }

        if self.__debug:
            print 'Sending TcpIp confirm request to %s with data: %s' % (requestUrl, tmpDataTcpIp2)
        self.__lastRequest = self.__sess.post(requestUrl, data=tmpDataTcpIp2, allow_redirects=False)




def scanner(data):
    ipaddr = data['ip_address']
    serial = data['serial_number']
    user = data['correct_user']
    pw = data['correct_pass']

    # DO NOT RUN THIS AGAINST PDUs with STATIC IPS!!!!
#    if ipaddr[:7] != "100.64.":
#        return False

    if len(user) == 0 or len(pw) == 0:
        print 'No user/pass for %s (s/n: %s)' % (ipaddr, serial)
        return False

    pdu = pduWeb(ipaddr, user, pw, debug=True)
    pdu.login()
    pdu.setSSH()
    pdu.setDns(primaryDns=settings['dns_s1'], secondaryDns=settings['dns_s2'], dnshostname=data['hostname'])
    pdu.setNtp(primaryNtp=settings['ntp_s1'], secondaryNtp=settings['ntp_s2'], ntpUpdateFrequency=settings['ntpUpdateFrequency'], timezone=settings['timezone'])
    pdu.setIdentification(hostname=data['hostname'], contact=settings['contact'], location=data['loc'])
#    pdu.resetTcpIpSettings()
    pdu.reboot()
    pdu.logout()


#    print 'Performing action: %s (s/n: %s): GENRESET1 {TCPIP}' % (ipaddr, serial)
#    tmpdata = { 'resetSelect': 'ResetExceptTCPIP', 'resetOnlyOptions': '?1', 'submit': 'Apply' }
#    resetres = pdusess.post('http://%s/%s/%s/Forms/genreset1' % (ipaddr, appPrefix, sessionToken), data=tmpdata)

#    print 'Performing action: %s (s/n: %s): RSTCNFRM1 {TCPIP}' % (ipaddr, serial)
#    tmpdata = { 'submit': 'Apply' }
#    resetres = pdusess.post('http://%s/%s/%s/Forms/rstcnfrm1' % (ipaddr, appPrefix, sessionToken), data=tmpdata)

#    print 'Performing action: %s (s/n: %s): GENRESET1 {REBOOT}' % (ipaddr, serial)
#    tmpdata = { 'resetSelect': 'Reboot', 'submit': 'Apply' }
#    resetres = pdusess.post('http://%s/%s/%s/Forms/genreset1' % (ipaddr, appPrefix, sessionToken), data=tmpdata)

#    print 'Performing action: %s (s/n: %s): RSTCNFRM1 {REBOOT}' % (ipaddr, serial)
#    tmpdata = { 'submit': 'Apply' }
#    resetres = pdusess.post('http://%s/%s/%s/Forms/rstcnfrm1' % (ipaddr, appPrefix, sessionToken), data=tmpdata)

#    print 'Performing action: %s (s/n: %s): LOGOUT' % (ipaddr, serial)
#    pdusess.get('http://%s/%s/%s/logout.htm' % (ipaddr, appPrefix, sessionToken))



#dccode = ''
dccode = cfg.getConfigValue('pdu', 'dccode')

url = '%s/pdu/getSettingsPerDC?dccode=%s' % (cfg.getConfigValue('pdu', 'api_base'), dccode)
r = reqget(url, headers={'SB-Auth-Key': cfg.getConfigValue('pdu', 'api_key')})
resp = r.json()
print resp

if 'settings' not in resp:
    exit()
else:
    settings = resp['settings']

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
