#!/usr/bin/python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(name='netconfig',
		version='1.4',
		description='AR Soft Network configuration tools',
		author='Andreas Roth',
		author_email='aroth@arsoft-online.com',
		url='http://www.arsoft-online.com/',
		packages=['arsoft', 
                    'arsoft.backup',
                    'arsoft.crypto',
                    'arsoft.ldap',
                    'arsoft.netconfig', 
                    ],
		scripts=[
            'certinfo',
            'jabber-send',
            'pxeconfig', 
            'slapd-config',
            'svnbackup'
            ],
		data_files=[ 
			('/etc/ldap/schema', ['schema/netconfig.schema']),
			('/etc/cron.hourly', ['cron/update-dhcpd-pxeclients']),
			]
		)
