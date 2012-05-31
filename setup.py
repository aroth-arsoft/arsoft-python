#!/usr/bin/python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(name='netconfig',
		version='1.4',
		description='AR Soft Network configuration tools',
		author='Andreas Roth',
		author_email='aroth@arsoft-online.com',
		url='http://www.arsoft-online.com/',
		packages=['arsoft', 'arsoft.netconfig', 'arsoft.backup'],
		scripts=[
            'pxeconfig', 
            'certinfo',
            'svnbackup'
            ],
		data_files=[ 
			('/etc/ldap/schema', ['schema/netconfig.schema']),
			('/etc/cron.hourly', ['cron/update-dhcpd-pxeclients']),
			]
		)
