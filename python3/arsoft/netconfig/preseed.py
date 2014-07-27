#!/usr/bin/python
# -*- coding: utf-8 -*-

from urlparse import urlparse
from urlparse import urlunparse

class PreseedInstaller(object):

	dn = ''
	cn = ''
	urls = []
	files = []
	arch = ''

	def __init__(self, r):
		"""Create a new LDAPSearchResult object."""
		self.dn = r.get_dn()
		self.cn = r.get_attr_value('cn')
		self.urls = r.get_attr_values('netconfigInstallerURL')
		self.arch = r.get_attr_value('netconfigInstallerArchitecture', '')
		self.files = r.get_attr_values('netconfigInstallerFile')

	def __repr__(self):
		ret = '  dn: ' + self.dn + '\n'
		ret = '  arch: ' + self.arch + '\n'
		for u in self.urls:
			ret += '  url: ' + u + '\n'
		for f in self.files:
			ret += '  file: ' + f + '\n'
		return ret

	def __str__(self):
		ret = 'dn: ' + self.dn + '\n'
		ret = 'arch: ' + self.arch + '\n'
		for u in self.urls:
			ret += 'url: ' + u + '\n'
		for f in self.files:
			ret += 'file: ' + f + '\n'
		return ret

class PreseedItem(object):
	"""A class to model a boot menu item.
	"""

	dn = ''
	cn = ''
	url = ''
	append = ''
	installer = {}

	def __init__(self, r):
		"""Create a new preseed item object."""
		self.dn = r.get_dn()
		self.cn = r.get_attr_value('cn')
		self.url = urlparse(r.get_attr_value('netconfigPreseedURL', ''))
		self.append = r.get_attr_value('netconfigPreseedAppend', '')
		
	def addInstaller(self, r):
		""" adds the given installer """
		installer = PreseedInstaller(r)
		self.installer[installer.arch] = installer
		
	def getURL(self, node=None):
		query = self.url.query
		if node is not None:
			if len(query) != 0:
				query += '&'
			query += 'node=' + node.name

		url = [self.url.scheme, self.url.netloc, self.url.path, self.url.params, query, self.url.fragment ]
		
		return urlunparse(url)
		
	def getAppend(self, node=None):
		ret = self.append
		if node is not None:
			if len(ret) != 0:
				ret += ' '
			ret += 'netcfg/get_hostname=' + node.name
		if len(ret) != 0:
			ret += ' '
		ret += 'netcfg/wireless_wep='
		if len(ret) != 0:
			ret += ' '
		ret += 'netcfg/choose_interface=eth0'
		if len(ret) != 0:
			ret += ' '
		ret += 'locale=en_US'
		if len(ret) != 0:
			ret += ' '
		ret += 'console-setup/layoutcode=us'
		return ret

	def __repr__(self):
		ret = 'dn: ' + self.dn + '\n'
		ret += 'url: ' + self.url.geturl() + '\n'
		ret += 'append: ' + self.append + '\n'
		for i in self.installer.values():
			ret += str(i)
		return ret
