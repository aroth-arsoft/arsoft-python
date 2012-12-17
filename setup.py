#!/usr/bin/python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(name='netconfig',
		version='1.34',
		description='AR Soft Python modules',
		author='Andreas Roth',
		author_email='aroth@arsoft-online.com',
		url='http://www.arsoft-online.com/',
		packages=['arsoft', 
                    'arsoft.backup',
                    'arsoft.config',
                    'arsoft.crypto',
                    'arsoft.cups',
                    'arsoft.efi',
                    'arsoft.fritzbox', 
                    'arsoft.ldap',
                    'arsoft.ldap.slapd',
                    'arsoft.mount',
                    'arsoft.nagios',
                    'arsoft.netconfig', 
                    'arsoft.nfs', 
                    'arsoft.openvpn'
                    ],
		scripts=[
            'certinfo',
            'fritzbox-status',
            'ini-util',
            'jabber-send',
            ],
		data_files=[ 
			('/etc/ldap/schema', ['schema/netconfig.schema']),
			('/etc/cron.hourly', ['cron/update-dhcpd-pxeclients']),
			('/etc/nagios-plugins/config', ['nagios/fritzbox.cfg', 'nagios/openvpn.cfg', 'nagios/kernel_modules.cfg']),
			('/usr/sbin', ['svnbackup', 'cups-admin', 'slapd-config', 'pxeconfig', 'efiinfo', 'nsswitch-config', 'nsswitch-ldap']),
			('/usr/lib/nagios/plugins', ['check_fritzbox', 'check_openvpn', 'check_kernel_modules']),
			]
		)
