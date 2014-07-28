#!/usr/bin/python
# -*- coding: utf-8 -*-

class MenuPosition:
	left = 0
	top = 0
	width = 0
	height = 0

	def __init__(self, str):
		self.fromString(str)

	def fromString(self, str):
		p = str.split(',')
		if len(p) >= 1 and len(p[0]):
			self.left = int(p[0])
		else:
			self.left = 0
		if len(p) >= 2 and len(p[1]):
			self.top = int(p[1])
		else:
			self.top = 0
		if len(p) >= 3 and len(p[2]):
			self.width = int(p[2])
		else:
			self.width = 0
		if len(p) >= 4 and len(p[3]):
			self.height = int(p[3])
		else:
			self.height = 0
        

class MenuItem:
	"""A class to model a boot menu item.
	"""

	dn = ''
	cn = ''
	title = ''
	childs = []
	kernel = ''
	append = ''
	arch = ''
	background = ''
	color = ''
	position = ''
	flags = ''
	local = None
	timeout = 0
	parent = None

	def __init__(self, r):
		"""Create a new LDAPSearchResult object."""
		self.dn = r.get_dn()
		self.cn = r.get_attr_value('cn')
		self.title = r.get_attr_value('netconfigMenuTitle', '')
		#print self.dn
		#print self.title
		self.childs = []
		self.kernel = r.get_attr_value('netconfigMenuKernel', '')
		self.arch = r.get_attr_value('netconfigArchitecture', '')
		self.background = r.get_attr_value('netconfigMenuBackground', '')
		self.append = r.get_attr_value('netconfigMenuAppend', '')
		self.color = r.get_attr_value('netconfigMenuColor', '')
		pos = r.get_attr_value('netconfigMenuPosition', '')
		if pos != '':
			self.position = MenuPosition(pos)
		else:
			self.position = None
		

		self.flags = {}
		for f in r.get_attr_values('netconfigMenuFlags'):
			e = f.split(' ')
			for x in e:
				n = x.find('=')
				if n >= 0:
					self.flags[x[0:n]] = x[n + 1:]
				else:
					self.flags[x] = None
		self.timeout = r.get_attr_value('netconfigMenuTimeout', -1)
		self.local = r.get_attr_value('netconfigMenuLocal', None)

	def addChild(self, child):
		child.parent = self
		self.childs.append(child)
		
	def hasFlag(self, flag):
		if flag in self.flags:
			return True
		else:
			return False

	def getFlag(self, flag):
		if flag in self.flags:
			return self.flags[flag]
		else:
			return None

	def __str__(self):
		return self.toString()

	def __repr__(self):
		print(self.toString())

	def toString(self, depth=0):
		string = (' ' * depth)
		string += self.title + '\n'
		for child in self.childs:
			string += child.toString(depth + 2)
		return string
