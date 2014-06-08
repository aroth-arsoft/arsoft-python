#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;
# vim: set ts=4 sw=4 tw=0 smarttab et

import ldap
import sys
import ldif
import string
import os.path
from StringIO import StringIO
from ldap.cidict import cidict
from logging import debug, info, exception, error, warning, handlers
import logging
import glob
#import yaml

import re
import socket

from ldapresult import *
from exception import *
from menu import *
from util import *
from preseed import *

from arsoft import ifconfig, IniFile

class NetconfigProperty(object):
    """A class to hold a net config property
    """

    netconfig = None
    path = ''
    name = ''
    comment = ''
    type = ''
    value = None
    arch = None

    def __init__(self, netconfig=None, path='', name='', comment='', type='', arch=None, value=None):
        self.netconfig = netconfig
        self.arch = arch
        self.path = path
        self.name = name
        self.comment = comment
        self.type = type
        self.value = value

    def fromLdap(self, result):
        self.path = result.get_dn()
        if result.has_attribute('netconfigpropertycomment'):
            self.comment = []
            ldapcomments = result.get_attr_values('netconfigpropertycomment')
            for c in ldapcomments:
                self.comment.append(self.netconfig._expandString(c))
        else:
            self.comment = []
        if result.has_attribute('netconfigpropertyvalue'):
            self.value = result.get_attr_values('netconfigpropertyvalue')
        else:
            self.value = []
        if result.has_attribute('netconfigpropertytype'):
            self.type = result.get_attr_values('netconfigpropertytype')[0]
        else:
            self.type = 'string'
        if result.has_attribute('netconfigarchitecture'):
            self.arch = result.get_attr_values('netconfigarchitecture')[0]
        else:
            self.arch = None

    def get(self, requesttype=None):
        if requesttype is None:
            requesttype = self.type
        return self._pack_value( requesttype, self.value)

    def _str2array(self, string):
        n = 1
        last = 0
        ret = []
        while n >= 0:
            n = string.find(' ', last)
            if n >= 0:
                tmp = string[last:n]
            else:
                tmp = string[last:]
            last = n + 1
            ret.append(tmp)
        return ret

    def _pack_value(self, typename, rawvalues):
        #print '_pack_value ' + self.path + ' ' + typename
        #print 'rawvalues ' + str(rawvalues)
        level = 0
        end = -1
        start = -1
        for i in range(0, len(typename)):
            if typename[i] == '(':
                if level == 0:
                    start = i
                level = level + 1
            elif typename[i] == ')':
                level = level - 1
            if level == 0 and start >= 0:
                end = i

        if start >= 0 and end >= 0:
            innertype = typename[start + 1: end]
            outertype = typename[0:start]
            #print "Inner " + innertype + " outer " + outertype
            typename = outertype

        # convert a given scalar into a array
        if type(rawvalues) != type([]):
            rawvalues = [rawvalues]

        if typename == 'string':
            ret = self.netconfig._expandString(string.join(rawvalues, ' '))
        elif typename == 'integer' or typename == 'int' or typename == 'unsigned' or typename == 'uint':
            try:
                ret = int(rawvalues[0])
            except ValueError:
                ret = None
        elif typename == 'float':
            try:
                ret = float(rawvalues[0])
            except ValueError:
                ret = None
        elif typename == 'boolean' or typename == 'bool':
            try:
                if rawvalues[0] == 'true' or rawvalues[0] == 'on' or rawvalues[0] == 'yes' or int(rawvalues[0]) != 0:
                    ret = True
                elif rawvalues[0] == 'false' or rawvalues[0] == 'off' or rawvalues[0] == 'no' or int(rawvalues[0]) == 0:
                    ret = False
                else:
                    ret = None
            except ValueError:
                ret = None
        elif typename == 'array' or typename == 'list':
            tmp = {}
            next = 0
            for rawvalue in rawvalues:
                #print rawvalue
                # in an array try to order the values
                start = rawvalue.find(':')
                digit = rawvalue[0:start]
                if digit.isdigit():
                    realvalue = rawvalue[start+1:].lstrip()
                    #print 'got digit %i value %s' % ( int(digit),  realvalue)
                    v = self._pack_value(innertype, self._str2array(realvalue))
                    #print 'type=' + innertype + ' '
                    tmp[int(digit)] = v
                else:
                    tmp[next] = self._pack_value(innertype, self._str2array(rawvalue))
                    next += 1
            ret = sortdict(tmp)
        elif typename == 'dict' or typename == 'map':
            n = innertype.find(',')
            if n >= 0:
                keytype = innertype[0:n]
                valuetype = innertype[n+1:]
            else:
                keytype = innertype
                valuetype = innertype
            ret = {}
            for rawvalue in rawvalues:
                # in an array try to order the values
                start = rawvalue.find(':')
                if start == -1:
                    start = rawvalue.find('=')
                    if start == -1:
                        continue
                key = self._pack_value(keytype, rawvalue[0:start])
                ret[key] = self._pack_value(valuetype, rawvalue[start+1:])
        elif typename == 'tuple':
            last = 0
            n = 1
            evalstr = ''
            idx = 0
            while n >= 0:
                n = innertype.find(',', last)
                if n >= 0:
                    curtype = innertype[last:n]
                else:
                    curtype = innertype[last:]
                if idx < len(rawvalues):
                    v = self._pack_value(curtype, rawvalues[idx]).__repr__()
                else:
                    v = 'None'
                if type(v) == type(0):
                    vstr = str(v)
                else:
                    vstr = v
                if len(evalstr):
                    evalstr = evalstr + ',' + vstr
                else:
                    evalstr = vstr
                idx = idx + 1
                last = n + 1
            #print evalstr
            ret = eval('(' + evalstr + ')' )
        elif typename == 'set':
            last = 0
            n = 1
            ret = set()
            idx = 0
            while n >= 0:
                n = innertype.find(',', last)
                if n >= 0:
                    curtype = innertype[last:n]
                else:
                    curtype = innertype[last:]
                v = self._pack_value(curtype, rawvalues[idx])
                ret.add(v)
                idx = idx + 1
                last = n + 1
        else:
            ret = None
        return ret

class NetconfigFile(object):
    """A class to hold a netconfig file
    """

    netconfig = None
    path = ''
    name = ''
    data = None
    owner = None
    group = None
    perm = 0666

    def __init__(self, netconfig=None, path='', name='', comment='', type='', arch=None, value=None):
        self.netconfig = netconfig
        self.arch = arch
        self.path = path
        self.name = name
        self.comment = comment
        self.type = type
        self.value = value

    def fromLdap(self, result):
        if result.has_attribute('netconfigFileName'):
            self.name = result.get_attr_values('netconfigFileName')[0]
        else:
            self.name = ''
        if result.has_attribute('netconfigFileOwner'):
            self.owner = result.get_attr_values('netconfigFileOwner')[0]
        else:
            self.owner = None
        if result.has_attribute('netconfigFileGroup'):
            self.group = result.get_attr_values('netconfigFileGroup')[0]
        else:
            self.group = None
        if result.has_attribute('netconfigFilePermission'):
            self.perm = result.get_attr_values('netconfigFilePermission')[0]
        else:
            self.perm = 0660
        if result.has_attribute('netconfigFileData'):
            self.data = result.get_attr_values('netconfigFileData')[0]
        else:
            self.data = None

class NetconfigArchive(object):
    """A class to hold a netconfig archive
    """

    netconfig = None
    path = ''
    name = ''
    data = None
    owner = None
    group = None
    perm = 0666

    def __init__(self, netconfig=None, path='', name='', comment='', type='', arch=None, value=None):
        self.netconfig = netconfig
        self.arch = arch
        self.path = path
        self.name = name
        self.comment = comment
        self.type = type
        self.value = value

    def fromLdap(self, result):
        if result.has_attribute('netconfigFileName'):
            self.name = result.get_attr_values('netconfigFileName')[0]
        else:
            self.name = ''
        if result.has_attribute('netconfigFileOwner'):
            self.owner = result.get_attr_values('netconfigFileOwner')[0]
        else:
            self.owner = None
        if result.has_attribute('netconfigFileGroup'):
            self.group = result.get_attr_values('netconfigFileGroup')[0]
        else:
            self.group = None
        if result.has_attribute('netconfigFilePermission'):
            self.perm = result.get_attr_values('netconfigFilePermission')[0]
        else:
            self.perm = 0660
        if result.has_attribute('netconfigFileData'):
            self.data = result.get_attr_values('netconfigFileData')[0]
        else:
            self.data = None
	def extract(self, dest, files=None):
			if files is not None:
					tmp = string.join(files, ' ')
			else:
					tmp = ''
			unpack(self.path, dest, tmp)

class NetconfigHardwareAddress(object):
	address = None
	def __init__(self, 	addr=None):
		if type(addr) != type([]):
			if addr.find(':') > 0:
				mac = addr.lower().split(':')
			elif addr.find('-') > 0:
				mac = addr.lower().split(':')
			else:
				mac = None
			self.address = mac
		else:
			self.address = addr
			
	def __str__(self):
		ret = string.join(self.address, ':')
		return ret
	
	def __repr__(self):
		print string.join(self.address, ':')
		
	def raw(self):
		return string.join(self.address, '')
		
	def toPXELinux(self):
		return '01-' + string.join(self.address, '-').lower()
		
class NetconfigNode(object):
    """A class to hold a netconfig node
    """

    netconfig = None
    dn = None
    name = None
    arch = None
    address = []
    yaml = None

    def __init__(self, netconfig=None, dn='', name='', arch=None, address=None, yaml=None):
        self.netconfig = netconfig
        self.dn = dn
        self.arch = arch
        self.name = name
        self.address = address
        self.yaml = yaml
    
    def fromLdap(self, result):
        self.dn = result.get_dn()
        
        if result.has_attribute('cn'):
            self.name = result.get_attr_values('cn')[0]
        else:
            self.name = ''
        if result.has_attribute('netconfigArchitecture'):
            self.arch = result.get_attr_values('netconfigArchitecture')[0]
        else:
            self.arch = None
        self.address = []
        if result.has_attribute('netconfigNodeAddress'):
            for a in result.get_attr_values('netconfigNodeAddress'):
                self.address.append(NetconfigHardwareAddress(a))
            
class NetconfigClass(object):
    """A class to hold a netconfig class
    """

    netconfig = None
    dn = None
    name = None
    
    def __init__(self, netconfig=None, dn='', name=''):
        self.netconfig = netconfig
        self.dn = dn
        self.name = name
    
    def fromLdap(self, result):
        self.dn = result.get_dn()
        
        if result.has_attribute('cn'):
            self.name = result.get_attr_values('cn')[0]
        else:
            self.name = ''
    

class Netconfig(object):
    """A class to access the AR Soft network configuration
    """

    m_ifconfig = None
    m_server = None
    m_ldap = None
    m_base = None
    m_user = None
    m_password = None
    m_node = None
    m_class = None
    m_interfaces = []
    m_environ = {}
    m_ldapConfigFiles = [ '~/.ldaprc', '/etc/ldap/ldap.conf']
    m_configFiles = [ '~/.netconfigrc', '/etc/netconfig/netconfig.conf' ]
    
    def __init__(self, server=None, user=None, password=None, base=None):
        self._loadLdapConfig()
        self._loadConfig()
        self.m_ifconfig = ifconfig()
        if server is not None:
            self.m_server = server
        if user is not None:
            self.m_user = user
        if password is not None:
            self.m_password = password
        if base is not None:
            self.m_base = base
        if self.m_server is not None:
			self.m_ldap = ldap.initialize(self.m_server)
			if self.m_user is not None and self.m_password is not None:
				debug('ldap user ' + str(self.m_user))
				debug('ldap passwd ' + str(self.m_password))
				self.m_ldap.simple_bind_s(self.m_user, self.m_password)
        self._initEnvironment()
        self.m_interfaces = ifconfig().getList()
        self._getNode()
        self._getClass()
        
    def _loadLdapConfig(self):
        #print self.m_configFiles
        config={}
        regexp = re.compile(r"(?P<cfgname>\w+)\s+(?P<cfgvalue>.*)$")
        for cfgfile in self.m_ldapConfigFiles:
            filename = os.path.expanduser(cfgfile)
            #debug('open ' + filename)
            if os.path.isfile(filename):
                f=open(filename, 'r')
                for line in f:
                    result = regexp.search(line)
                    if result != None:
                        name = result.group('cfgname').lower()
                        value = result.group('cfgvalue');
                        if value == None:
                            value = ''
                        else:
                            value = value.strip('\'"')
                        config[name] = value
                f.close()
        if config.has_key('uri'):
            self.m_server = config['uri']
        if config.has_key('host'):
            self.m_server = config['host']
        if config.has_key('base'):
            self.m_base = config['base']
        
        
    def _loadConfig(self):
        config={}
        #print self.m_configFiles
        regexp = re.compile(r"(?P<cfgname>\w+)\s+(?P<cfgvalue>.*)$")
        for cfgfile in self.m_configFiles:
            filename = os.path.expanduser(cfgfile)
            #debug('open ' + filename)
            if os.path.isfile(filename):
                f=open(filename, 'r')
                for line in f:
                    result = regexp.search(line)
                    if result != None:
                        name = result.group('cfgname')
                        value = result.group('cfgvalue');
                        if value == None:
                            value = ''
                        else:
                            value = value.strip('\'"')
                        config[name] = value
                f.close()
        if config.has_key('server'):
            self.m_server = config['server']
        if config.has_key('base'):
            self.m_base = config['base']
        if config.has_key('user') and len(config['user']) != 0:
            self.m_user = config['user']
        if config.has_key('password') and len(config['password']) != 0:
            self.m_password = config['password']
            
    def _initEnvironment(self):
        self.m_environ['bindir'] = '/usr/bin'
        self.m_environ['sbindir'] = '/usr/sbin'
        self.m_environ['sharedir'] = '/usr/share'
        self.m_environ['libdir'] = '/usr/lib'
        self.m_environ['mandir'] = '/usr/share/man'
        self.m_environ['infodir'] = '/usr/share/info'
        if os.path.exists('/etc/lsb-release'):
            f = IniFile('/etc/lsb-release')
            self.m_environ['distributionId'] = f.get('default', 'DISTRIB_ID', '')
            self.m_environ['distributionVersion'] = f.get('default', 'DISTRIB_RELEASE', '')
            self.m_environ['distributionCodename'] = f.get('default', 'DISTRIB_CODENAME', '')
            self.m_environ['distributionDesc'] = f.get('default', 'DISTRIB_DESCRIPTION', '')

    def _getNode(self):
        self.m_node = None
        for i in self.m_interfaces:
            filter="(&(objectClass=netconfigNode)(netconfigNodeAddress=%s))"%i['hwaddr']
#            print "search base=%s, filter=%s" % (self.m_base ,filter)
            try:
                result_id = self.m_ldap.search_s(self.m_base, ldap.SCOPE_SUBTREE, filter, ['dn','cn','netconfigNodeAddress','netconfigArchitecture'])
            except ldap.NO_SUCH_OBJECT:
                break
            results = self._get_search_results(result_id)
            if len(results) > 0:
#                print "got node %s " %results[0].get_dn()
                self.m_node = NetconfigNode(self)
                self.m_node.fromLdap(results[0])
                break
                
    def _getClassByFilter(self, filter):
        ret = None
        #print "search base=%s, filter=%s" % (self.m_base ,filter)
        try:
            result_id = self.m_ldap.search_s(self.m_base, ldap.SCOPE_SUBTREE, filter, ['dn','cn'])
            results = self._get_search_results(result_id)
            if len(results) > 0:
                ret = NetconfigClass(self)
                ret.fromLdap(results[0])
    #           print "got class %s " %self.m_class['dn']
            else:
                ret = None
        except ldap.NO_SUCH_OBJECT:
            ret = None
        return ret
                
    def _getDefaultClass(self):
        return self._getClassByFilter("(&(objectClass=netconfigClass)(cn=default))")
        
    def _getNodeClass(self):
        return self._getClassByFilter("(&(objectClass=netconfigClass)(netconfigClassNode=%s))"%self.m_node.dn)

    def _getClass(self):
        if self.m_node != None:
            self.m_class = self._getNodeClass()
        if self.m_class is None:
            self.m_class = self._getDefaultClass()

        if self.m_class == None:
            if self.m_node != None:
                raise NetconfigException("No class for node " + str(self.m_node) + " found (possible missing configuration)")
                
    def getNode(self, name=None, address=None):
        if name is not None:
            filter="(&(objectClass=netconfigNode)(|(cn=" + name + ")(netconfigName=" + name + ")))"
        elif address is not None:
            filter="(&(objectClass=netconfigNode)(netconfigNodeAddress=" + address + "))"
        else:
            return None
        ret = None
        try:
            result_id = self.m_ldap.search_s(self.m_base, ldap.SCOPE_SUBTREE, filter, ['dn','cn','netconfigNodeAddress','netconfigArchitecture'])
            results = self._get_search_results(result_id)
            for r in results:
                ret = NetconfigNode(self)
                ret.fromLdap(r)
        except ldap.NO_SUCH_OBJECT:
            pass
        return ret
            
    def getNodes(self):
        filter="(objectClass=netconfigNode)"
        ret = []
        try:
            result_id = self.m_ldap.search_s(self.m_base, ldap.SCOPE_SUBTREE, filter, ['dn','cn','netconfigNodeAddress','netconfigArchitecture'])
            results = self._get_search_results(result_id)
            for r in results:
                node = NetconfigNode(self)
                node.fromLdap(r)
                ret.append(node)
        except ldap.NO_SUCH_OBJECT:
            pass
    
        #ret = []
        #node_yaml_files = glob.glob('/home/aroth/tmp/*.yaml')
        #for node_yaml in node_yaml_files:
            #f = open(node_yaml, 'r')
            #content = f.readlines();
            #if content[0].find('ruby/object:Puppet::Node'):
                #y = yaml.load(string.join(content[1:], '\n'))
                #f.close()
                #if 'parameters' in y:
                    #params = y['parameters']
                    #if 'architecture' in params:
                        #addresses = []
                        #for iface in params['interfaces'].split(','):
                            #mac = 'macaddress_' + iface
                            #if mac in params:
                                #addresses.append(params[mac])
                        #node = NetconfigNode(self, node_yaml, y['name'], params['architecture'], addresses, y)
                        #ret.append(node)
        
        return ret
        
        
    def getBootMenus(self):
        filter="(&(objectClass=netconfigMenu)(cn=default))"
        ret = None
        try:
            regexp_order = re.compile(r"(?P<order>\{[0-9]+\})*(?P<value>.*)$")
            
            result_id = self.m_ldap.search_s(self.m_base, ldap.SCOPE_SUBTREE, filter, ['dn','cn','netconfigMenuTitle',
                                                                                        'netconfigArchitecture','netconfigMenuBackground',
                                                                                        'netconfigMenuColor','netconfigMenuPosition',
                                                                                        'netconfigMenuLocal','netconfigMenuFlags',
                                                                                        'netconfigMenuChild','netconfigMenuKernel',
                                                                                        'netconfigMenuAppend'])
            results = self._get_search_results(result_id)
            if len(results):
                dn = results[0].get_dn()
                ret = MenuItem(results[0])
                for r in results:
                    childs = []
                    next = 0
                    all_childs = sorted(r.get_attr_values('netconfigMenuChild'))
                    for rawvalue in all_childs:
                        # in an array try to order the values
                        result = regexp_order.search(rawvalue)
                        if result != None:
                            value = result.group('value');
                        else:
                            value = rawvalue
                        childs.append(value)

                    for child in childs:
                        self._getSubMenus(child,ret)
        except ldap.NO_SUCH_OBJECT:
            pass
        #print ret.toString()
        return ret

    def _getSubMenus(self, base, menu):
        filter="(objectClass=netconfigMenu)"
        ret = []
        try:
            #print 'look for sub menus in ' + base
            result_id = self.m_ldap.search_s(base, ldap.SCOPE_BASE, filter, ['dn','cn','netconfigMenuTitle',
                                                                                        'netconfigArchitecture','netconfigMenuBackground',
                                                                                        'netconfigMenuColor','netconfigMenuPosition',
                                                                                        'netconfigMenuLocal','netconfigMenuFlags',
                                                                                        'netconfigMenuChild','netconfigMenuKernel',
                                                                                        'netconfigMenuAppend'])
            results = self._get_search_results(result_id)
            for r in results:
                childmenu = MenuItem(r)
                childs = {}
                next = 0
                for rawvalue in r.get_attr_values('netconfigMenuChild'):
                    # in an array try to order the values
                    start = rawvalue.find(':')
                    digit = rawvalue[0:start]
                    if digit.isdigit():
                        realvalue = rawvalue[start+1:].lstrip()
                        childs[int(digit)] = realvalue
                    else:
                        childs[next] = rawvalue
                        next += 1
                for child in childs.values():
                    #print child
                    self._getSubMenus(child,childmenu)
                menu.addChild(childmenu)
        except ldap.NO_SUCH_OBJECT:
            pass
        except ldap.INVALID_DN_SYNTAX:
            pass
        return ret

    def getPreseed(self, name=None):
        if name is None:
            filter="(objectClass=netconfigPreseedConfig)"
        else:
            filter="(&(objectClass=netconfigPreseedConfig)(cn=" + name + "))"
        ret = None
        try:
            result_id = self.m_ldap.search_s(self.m_base, ldap.SCOPE_SUBTREE, filter, ['dn','cn','netconfigPreseedURL','netconfigPreseedAppend'])
            results = self._get_search_results(result_id)
            for r in results:
                item = PreseedItem(r)
                if name is not None and len(results) == 1:
                    ret = item
                else:
                    if ret is None:
                        ret = [item]
                    else:
                        ret.append(item)

                # now get the installers for this item
                installer_filter = "(objectClass=netconfigPreseedInstaller)"
                try:
                    #print 'base ' + r.get_dn()
                    #print 'filer '+ installer_filter
                    result_id = self.m_ldap.search_s(r.get_dn(), ldap.SCOPE_SUBTREE, installer_filter, ['dn','cn','netconfigInstallerURL','netconfigArchitecture','netconfigInstallerFile'])
                    results = self._get_search_results(result_id)
                    for r in results:
                        item.addInstaller(r)
                except ldap.NO_SUCH_OBJECT:
                    pass

        except ldap.NO_SUCH_OBJECT:
            pass
        return ret

    def _get_search_results(self, results):
        """Given a set of results, return a list of LDAPSearchResult
        objects.
        """
        res = []
    
        if type(results) == tuple and len(results) == 2 :
            (code, arr) = results
        elif type(results) == list:
            arr = results
    
        if len(results) == 0:
            return res
    
        for item in arr:
            res.append( LDAPSearchResult(item) )
    
        return res
    def _expandString(self, str):
        for (e, v) in self.m_environ.items():
            str = str.replace('$' + e,v)
        return str
    def addEnvironment(self, environ):
        for (n, v) in environ.items():
            self.m_environ[n] = v
        
    def getString(self, name, default_value=''):
        return self.get(name, 'string', default_value);
    
    def getInteger(self, name, default_value=0):
        return self.get(name, 'integer', default_value);

    def getBoolean(self, name, default_value=False):
        return self.get(name, 'boolean', default_value);

    def getTuple(self, name, form, default_value=None):
        return self.get(name, 'tuple(' + form + ')', default_value);
    
    def getStringList(self, name, default_value=[]):
        return self.get(name, 'list(string)', default_value);
    
    def getIntegerList(self, name, default_value=[]):
        return self.get(name, 'list(integer)', default_value);
    
    def getTupleList(self, name, form, default_value=None):
        return self.get(name, 'list(tuple(' + form + '))', default_value);

    def get(self, name, requesttype, default_value=None):
        return self.getProperty(name, requesttype, default_value).get(requesttype)

    def getProperty(self, name, requesttype, default_value=None):
        path = name
        name=name.split('/').pop();
        prop = NetconfigProperty(self, value=default_value)
        ret = self._getProperty(self.m_node.dn, path, requesttype, prop)
        if ret == False:
            ret = self._getProperty(self.m_class['dn'], path, requesttype, prop)
#            if ret == True:
 #               print value
        return prop

    def _finddir(self, base, name, fullpath=False):
        elems=name.split('/');
        if fullpath == False:
            cn=elems.pop()
        else:
            cn=None
        if len(elems) == 0:
            pathok=True
        else:
            pathok=False
        #print "elems %s cn=%s" % (elems, cn)
        for ouname in elems:
            filter="(&(objectClass=organizationalUnit)(ou=" + ouname + "))"
            #print "finddir search base=%s, filter=%s" % (base ,filter)
            try:
                result_id = self.m_ldap.search_s(base, ldap.SCOPE_SUBTREE, filter, ['dn'])
                results = self._get_search_results(result_id)
                #print results
                if len(results) > 0:
                    base = results[0].get_dn()
                    pathok=True
                else:
                    pathok=False
            except ldap.NO_SUCH_OBJECT:
                pathok=False
            if pathok == False:
                break;
        return (pathok, base)
        

    def _getProperty(self, base, name, requesttype, prop):
        cn=name.split('/').pop();

        (pathok, base) = self._finddir(base, name)

        #print 'name %s pathok %i' % (name, pathok)
        if pathok == True:
            #print self.m_node
            filter='(&(objectClass=netconfigProperty)(|(!(netconfigArchitecture=*))(netconfigArchitecture='+self.m_node.arch+'))(|(cn=' + cn + ')(netconfigPropertyName=' + cn + ')))'
            #print "search base=%s, filter=%s" % (base ,filter)
            result_id = self.m_ldap.search_s(base, ldap.SCOPE_SUBTREE, filter, ['cn','netconfigpropertyname','netconfigpropertytype',
                                                                                'netconfigpropertyvalue','netconfigpropertycomment',
                                                                                'netconfigarchitecture'])
            results = self._get_search_results(result_id)
            for result in results:
                prop.fromLdap(result)
                ret = True
            else:
                ret = False
        else:
            ret = False
        #print "got value %s" % ret
        return ret;

    def getFile(self, name):
        file=None
        ret = self._getFile(self.m_node.dn, name, file)
        if ret == False:
            ret = self._getFile(self.m_class['dn'], name, file)
        return file

    def _getFile(self, base, name, file):
        cn=name.split('/').pop();
        (pathok, base) = self._finddir(base, name)
        ret = False
        if pathok == True:
            #print "base for enum " + base
            filter='(&(objectClass=netconfigFile)(|(!(netconfigArchitecture=*))(netconfigArchitecture='+self.m_node.arch+'))(|(cn=' + cn + ')(netconfigFileName=' + cn + ')))'
            #print "search base=%s, filter=%s" % (base ,filter)
            result_id = self.m_ldap.search_s(base, ldap.SCOPE_ONELEVEL, filter, None)
            results = self._get_search_results(result_id)
            file = None
            for result in results:
                file = NetconfigFile()
                file.fromLdap(result)
                ret = True
        else:
            file = None
        return ret

    def enum(self, name):
        name=name.split('/').pop();
        #print 'name ' + name
        list=[]
        ret = self._enum(self.m_class['dn'], name, list)
        ret = self._enum(self.m_node.dn, name, list)
        return list

    def _enum(self, base, name, list):
        ret = False
        (pathok, base) = self._finddir(base, name, True)
        #print "new base " + base
        if pathok == True:
            filter="(|(objectClass=organizationalUnit)(objectClass=netconfigProperty))"
            #print "_enum search base=%s, filter=%s" % (base ,filter)
            result_id = self.m_ldap.search_s(base, ldap.SCOPE_ONELEVEL, filter, None)
            results = self._get_search_results(result_id)
            for result in results:
                elemname = ''
                if result.has_attribute('cn'):
                    elemname = result.get_attr_values('cn')[0]
                elif result.has_attribute('ou'):
                    elemname = result.get_attr_values('ou')[0]
                #print elemname
                if len(elemname):
                    list.append(name + '/' + elemname)
                    ret = True
        else:
            list = []
        return ret

############################################################################
if __name__=='__main__':
    cfg = Netconfig()
    prop = NetconfigProperty(cfg)
    #print prop._pack_value('string', ['hello', 'world'])
    #print prop._pack_value('array(string)', ['hello', 'world'])
    #print prop._pack_value('array(string)', ['2:hello', '1:world'])
    #print prop._pack_value('dict(int,string)', ['2:hello', '1:world'])
    #print prop._pack_value('dict(string,string)', ['2=hello', '1=world'])
    #print prop._pack_value('list(bool)', ['2:hello', '1:world'])
    #print prop._pack_value('list(int)', ['2:hello', '1:world'])
#    print prop._pack_value('tuple(int,int)', ['2', '1'])
 #   print prop._pack_value('tuple(string,string,string,string)', ['2', '1'])
  #  print prop._pack_value('list(tuple(string,string,string,string))', ['2', '1'])
    #print prop._pack_value('list(tuple(int,int))', ['2 1', '5 7'])
    #print prop._pack_value('set(int,int,int)', ['20', '1', '2'])
    #print prop._pack_value('array(dict(int,string))', ['2:17=hello 18=a', '1:89=world'])
    
    #f = cfg.getFile('tftp/pxelinux.0')
    #print f
