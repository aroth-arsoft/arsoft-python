#!/usr/bin/python
import os, sys
import argparse

import pycurl
import libxml2
from datetime import datetime, timedelta

class FritzBox(object):

    def __init__(self, hostname='fritz.box', port=49000):
        self._hostname = hostname
        self._port = port
        self._status = None
        self._wanAddress = None
        self._addonInfo = None
        self._dslLinkInfo = None
        self._commonLinkProperties = None
        self._userList = None
        self._callLists = {}

    class Request:
        def __init__(self, uri, urn, action):
            self._uri = uri
            self._urn = urn
            self._action = action
            
        def data(self):
            return '<?xml version="1.0" encoding="utf-8"?>' +\
                    '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" ' +\
                    's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">' +\
                    '<s:Body>' +\
                    '<u:' + self._action + ' xmlns:u="urn:' + self._urn + '" />' +\
                    '</s:Body>' +\
                    '</s:Envelope>'

    class Response:
        def __init__(self):
            self.contents = ''
        def body_callback(self, buf):
            self.contents = self.contents + buf

    def _sendRequest(self, request, verbose=False):
        resp = FritzBox.Response()
        c = pycurl.Curl()
        url = 'http://' + self._hostname + ':' + str(self._port) + request._uri
        try:
            data = request.data()
            try:
                if verbose:
                    print(('C: ' + url))
                    print(('C: ' + data))
                c.setopt(pycurl.URL, url)
                c.setopt(pycurl.POST, 1)
                c.setopt(pycurl.POSTFIELDS, data)
                c.setopt(pycurl.INFILESIZE, len(data))
                c.setopt(pycurl.WRITEFUNCTION, resp.body_callback)
                c.setopt(pycurl.CONNECTTIMEOUT, 30)
                c.setopt(pycurl.TIMEOUT, 300)
                c.setopt(pycurl.HTTPHEADER, ['SOAPACTION: "urn:' + request._urn + '#' + request._action + '"', 'CONTENT-TYPE: text/xml;', 'User-Agent: nagios'])
                c.perform()
                if verbose:
                    print(('S: ' + resp.contents))
                ret = True
            except Exception as e:
                print("ERROR - HTTP request to UPNP server not possible " + str(e))
                ret = False
        finally:
            c.close()
        
        if ret:
            return resp
        else:
            return None

    def _retrieveStatusInfo(self):
        response = self._sendRequest( FritzBox.Request('/upnp/control/WANIPConn1', 'schemas-upnp-org:service:WANIPConnection:1', 'GetStatusInfo') )
        if response is not None:
            self._status = {}
            ret = False
            try:
                doc = libxml2.parseDoc(response.contents)
                ctxt = doc.xpathNewContext()
                ctxt.xpathRegisterNs('s',"http://schemas.xmlsoap.org/soap/envelope/")
                ctxt.xpathRegisterNs('u',"urn:schemas-upnp-org:service:WANIPConnection:1")
                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetStatusInfoResponse/NewConnectionStatus')
                self._status['connectionstatus'] = elements[0].content
                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetStatusInfoResponse/NewUptime')
                self._status['connectDuration'] = int(elements[0].content)
                self._status['connectTime'] = datetime.now() - timedelta(seconds=self._status['connectDuration'])
                ret = True
            finally:
                doc.freeDoc()
        else:
            self._status = None
            ret = False
        return ret

    def _retrieveWANAddress(self, pre_os6=False):
        if pre_os6:
            request = FritzBox.Request('/upnp/control/WANCommonIFC1', 'schemas-upnp-org:service:WANPPPConnection:1', 'GetExternalIPAddress')
        else:
            request = FritzBox.Request('/upnp/control/WANIPConn1', 'schemas-upnp-org:service:WANIPConnection:1', 'GetExternalIPAddress')
        response = self._sendRequest( request )
        if response is not None:
            self._wanAddress = ''
            ret = False
            try:
                doc = libxml2.parseDoc(response.contents)
                ctxt = doc.xpathNewContext()
                ctxt.xpathRegisterNs('s',"http://schemas.xmlsoap.org/soap/envelope/")
                if pre_os6:
                    ctxt.xpathRegisterNs('u',"urn:schemas-upnp-org:service:WANPPPConnection:1")
                else:
                    ctxt.xpathRegisterNs('u',"urn:schemas-upnp-org:service:WANIPConnection:1")
                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetExternalIPAddressResponse/NewExternalIPAddress')
                if elements:
                    self._wanAddress = elements[0].content
                    ret = True
                else:
                    self._wanAddress = None
                    ret = False
            finally:
                doc.freeDoc()
        else:
            self._wanAddress = None
            ret = False
        return ret

    def _retrieveAddonInfo(self):
        response = self._sendRequest( FritzBox.Request('/upnp/control/WANCommonIFC1', 'schemas-upnp-org:service:WANCommonInterfaceConfig:1', 'GetAddonInfos') )
        if response is not None:
            self._addonInfo = {}
            ret = False
            try:
                doc = libxml2.parseDoc(response.contents)
                ctxt = doc.xpathNewContext()
                ctxt.xpathRegisterNs('s',"http://schemas.xmlsoap.org/soap/envelope/")
                ctxt.xpathRegisterNs('u',"urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1")
                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetAddonInfosResponse/NewDNSServer1')
                dnsserver1 = elements[0].content
                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetAddonInfosResponse/NewDNSServer2')
                dnsserver2 = elements[0].content
                self._addonInfo['dnsserver'] = [ dnsserver1, dnsserver2 ]

                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetAddonInfosResponse/NewVoipDNSServer1')
                dnsserver1 = elements[0].content
                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetAddonInfosResponse/NewVoipDNSServer2')
                dnsserver2 = elements[0].content
                self._addonInfo['voipdnsserver'] = [ dnsserver1, dnsserver2 ]

                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetAddonInfosResponse/NewByteSendRate')
                self._addonInfo['sendRateByte'] = int(elements[0].content)
                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetAddonInfosResponse/NewByteReceiveRate')
                self._addonInfo['receiveRateByte'] = int(elements[0].content)
                
                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetAddonInfosResponse/NewPacketSendRate')
                self._addonInfo['sendRatePacket'] = int(elements[0].content)
                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetAddonInfosResponse/NewPacketReceiveRate')
                self._addonInfo['receiveRatePacket'] = int(elements[0].content)

                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetAddonInfosResponse/NewTotalBytesSent')
                self._addonInfo['sendTotalRateByte'] = int(elements[0].content)
                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetAddonInfosResponse/NewTotalBytesReceived')
                self._addonInfo['receiveTotalByte'] = int(elements[0].content)
                ret = True
            finally:
                doc.freeDoc()
        else:
            self._addonInfo = None
            ret = False
        return ret

    def _retrieveCallLists(self, user):
        response = self._sendRequest( FritzBox.Request('/upnp/control/foncontrol', 'schemas-upnp-org:service:device:foncontrol:1', 'GetCallLists') )
        if response is not None:
            self._callLists[user] = []
            ret = False
            try:
                doc = libxml2.parseDoc(response.contents)
                ctxt = doc.xpathNewContext()
                ctxt.xpathRegisterNs('s',"http://schemas.xmlsoap.org/soap/envelope/")
                ctxt.xpathRegisterNs('u',"urn:schemas-upnp-org:service:WANIPConnection:1")
                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetExternalIPAddressResponse/NewExternalIPAddress')
                #self._wanAddress = elements[0].content
                ret = True
            finally:
                doc.freeDoc()
        else:
            self._callLists[user] = None
            ret = False
        return ret

    def _retrieveUserList(self):
        response = self._sendRequest( FritzBox.Request('/upnp/control/foncontrol', 'schemas-upnp-org:service:device:foncontrol:1', 'GetUserList'), True )
        if response is not None:
            self._userList = []
            ret = False
            print((response.contents))
            try:
                doc = libxml2.parseDoc(response.contents)
                ctxt = doc.xpathNewContext()
                ctxt.xpathRegisterNs('s',"http://schemas.xmlsoap.org/soap/envelope/")
                ctxt.xpathRegisterNs('u',"urn:schemas-upnp-org:service:device:foncontrol:1")
                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetUserListResponse/UserList')
                #self._wanAddress = elements[0].content
                ret = True
            finally:
                doc.freeDoc()
        else:
            self._userList = None
            ret = False
        return ret

    def _retrieveDSLLinkInfo(self):
        response = self._sendRequest( FritzBox.Request('/upnp/control/WANDSLLinkC1', 'schemas-upnp-org:service:WANDSLLinkConfig:1', 'GetDSLLinkInfo') )
        if response is not None:
            self._dslLinkInfo = {}
            ret = False
            try:
                doc = libxml2.parseDoc(response.contents)
                ctxt = doc.xpathNewContext()
                ctxt.xpathRegisterNs('s',"http://schemas.xmlsoap.org/soap/envelope/")
                ctxt.xpathRegisterNs('u',"urn:schemas-upnp-org:service:WANDSLLinkConfig:1")
                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetDSLLinkInfoResponse/NewLinkType')
                self._dslLinkInfo['linktype'] = elements[0].content
                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetDSLLinkInfoResponse/NewLinkStatus')
                self._dslLinkInfo['status'] = elements[0].content
                ret = True
            finally:
                doc.freeDoc()
        else:
            self._dslLinkInfo = None
            ret = False
        return ret

    def _retrieveCommonLinkProperties(self):
        response = self._sendRequest( FritzBox.Request('/upnp/control/WANCommonIFC1', 'schemas-upnp-org:service:WANCommonInterfaceConfig:1', 'GetCommonLinkProperties') )
        if response is not None:
            self._commonLinkProperties = {}
            ret = False
            try:
                doc = libxml2.parseDoc(response.contents)
                ctxt = doc.xpathNewContext()
                ctxt.xpathRegisterNs('s',"http://schemas.xmlsoap.org/soap/envelope/")
                ctxt.xpathRegisterNs('u',"urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1")
                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetCommonLinkPropertiesResponse/NewWANAccessType')
                self._commonLinkProperties['wanaccesstype'] = elements[0].content
                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetCommonLinkPropertiesResponse/NewLayer1UpstreamMaxBitRate')
                self._commonLinkProperties['upstreammaxbiterate'] = int(elements[0].content)
                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetCommonLinkPropertiesResponse/NewLayer1DownstreamMaxBitRate')
                self._commonLinkProperties['downstreammaxbitrate'] = int(elements[0].content)
                elements = ctxt.xpathEval('/s:Envelope/s:Body/u:GetCommonLinkPropertiesResponse/NewPhysicalLinkStatus')
                self._commonLinkProperties['physicallinkstatus'] = elements[0].content
                ret = True
            finally:
                doc.freeDoc()
        else:
            self._commonLinkProperties = None
            ret = False
        return ret


    def connectTime(self):
        if self._status is None:
            self._retrieveStatusInfo()
        if self._status is not None:
            return self._status['connectTime']
        else:
            return None
    def connectDuration(self):
        if self._status is None:
            self._retrieveStatusInfo()
        if self._status is not None:
            return self._status['connectDuration']
        else:
            return None

    def connectionStatus(self):
        if self._status is None:
            self._retrieveStatusInfo()
        if self._status is not None:
            return self._status['connectionstatus']
        else:
            return None
            
    def dslLinkStatus(self):
        if self._dslLinkInfo is None:
            self._retrieveDSLLinkInfo()
        if self._dslLinkInfo is not None:
            return self._dslLinkInfo['status']
        else:
            return None

    def physicalLinkStatus(self):
        if self._commonLinkProperties is None:
            self._retrieveCommonLinkProperties()
        if self._commonLinkProperties is not None:
            return self._commonLinkProperties['physicallinkstatus']
        else:
            return None

    def physicalLinkUpStream(self):
        if self._commonLinkProperties is None:
            self._retrieveCommonLinkProperties()
        if self._commonLinkProperties is not None:
            return self._commonLinkProperties['upstreammaxbiterate']
        else:
            return None

    def physicalLinkDownStream(self):
        if self._commonLinkProperties is None:
            self._retrieveCommonLinkProperties()
        if self._commonLinkProperties is not None:
            return self._commonLinkProperties['downstreammaxbitrate']
        else:
            return None
    
    def isConnected(self):
        cxnstat = self.connectionStatus()
        return True if cxnstat == 'Connected' else False
        
    def isDSLConnected(self):
        cxnstat = self.dslLinkStatus()
        return True if cxnstat == 'Up' else False

    def isPhysicalConnected(self):
        cxnstat = self.physicalLinkStatus()
        return True if cxnstat == 'Up' else False
        
    def wanAddress(self):
        if self._wanAddress is None:
            self._retrieveWANAddress()
        if self._wanAddress is not None:
            return self._wanAddress
        else:
            return None

    def dnsServer(self):
        if self._addonInfo is None:
            self._retrieveAddonInfo()
        if self._addonInfo is not None:
            return self._addonInfo['dnsserver']
        else:
            return None
            
    def userList(self):
        if self._userList is None:
            self._retrieveUserList()
        if self._userList is not None:
            return self._userList
        else:
            return None

    def callList(self, user):
        if self._callsList is None:
            self._retrieveCallLists(user)
        if self._callsList is not None:
            if user in self._callLists:
                return self._callLists[user]
            else:
                return []
        else:
            return None


    def reconnect(self):
        response = self._sendRequest( FritzBox.Request('/upnp/control/WANIPConn1', 'schemas-upnp-org:service:WANIPConnection:1', 'ForceTermination') )
        if response is not None:
            ret = True
        else:
            ret = False
        return ret
