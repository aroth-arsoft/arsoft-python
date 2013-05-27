#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from distutils.core import setup

setup(name='arsoft-python',
		version='1.62',
		description='AR Soft Python modules',
		author='Andreas Roth',
		author_email='aroth@arsoft-online.com',
		url='http://www.arsoft-online.com/',
		packages=['arsoft', 
                    'arsoft.backup',
                    'arsoft.config',
                    'arsoft.crypto',
                    'arsoft.cups',
                    'arsoft.disks',
                    'arsoft.efi',
                    'arsoft.fritzbox', 
                    'arsoft.kerberos',
                    'arsoft.ldap',
                    'arsoft.ldap.slapd',
                    'arsoft.mail',
                    'arsoft.mount',
                    'arsoft.nagios',
                    'arsoft.netconfig', 
                    'arsoft.nfs', 
                    'arsoft.openvpn',
                    'arsoft.trac',
                    'arsoft.trac.plugins',
                    'arsoft.web',
                    'arsoft.web.templatetags',
                    'arsoft.xdg',
                    'arsoft.xmpp'
                    ],
		scripts=[
            'certinfo',
            'fritzbox-status',
            'ini-util',
            'jabber-send',
            'jabber-daemon',
            'trac-sqlite2mysql',
            'trac-svn2git',
            'trac-manage',
            'arsoft-backup',
            'edskmgr',
            'alog'
            ],
		data_files=[ 
			('/etc/ldap/schema', ['schema/netconfig.schema']),
			('/etc/cron.hourly', ['cron/update-dhcpd-pxeclients']),
			('/etc/init', ['upstart/jabber-daemon.conf']),
			('/etc', ['config/jabber-daemon.conf']),
			('/etc/nagios-plugins/config', ['nagios/fritzbox.cfg', 'nagios/openvpn.cfg', 'nagios/kernel_modules.cfg', 'nagios/xmpp_notify.cfg', 'nagios/puppet_agent.cfg', 'nagios/weather.cfg', 'nagios/ipp.cfg']),
			('/usr/sbin', ['svnbackup', 'cups-admin', 'slapd-config', 'pxeconfig', 'efiinfo', 'nsswitch-config', 'nsswitch-ldap', 'autofs-ldap-auth', 'managehosts', 'heimdal-password-expire']),
			('/usr/lib/nagios', ['send_xmpp_notification']),
			('/usr/lib/nagios/plugins', ['check_fritzbox', 'check_openvpn', 'check_kernel_modules', 'check_puppet_agent', 'check_weather', 'check_ipp']),
			('/usr/lib/nagios/plugins/test_data', ['test_data/check_ipp.test', 'test_data/check_ipp_jobs.test', 'test_data/check_ipp_completed_jobs.test']),
			('/lib/udev', [ 'edskmgr-support/external-disk' ]),
			('/lib/udev/rules.d', [ 'edskmgr-support/88-external-disk.rules' ]),
			]
		)
