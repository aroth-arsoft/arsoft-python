#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from distutils.core import setup

setup(name='arsoft-python',
		version='1.127',
		description='AR Soft Python modules',
		author='Andreas Roth',
		author_email='aroth@arsoft-online.com',
		url='http://www.arsoft-online.com/',
		packages=['arsoft', 
                    'arsoft.backup',
                    'arsoft.backup.plugins',
                    'arsoft.config',
                    'arsoft.crypto',
                    'arsoft.cups',
                    'arsoft.disks',
                    'arsoft.efi',
                    'arsoft.eiscp',
                    'arsoft.fritzbox', 
                    'arsoft.kerberos',
                    'arsoft.git',
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
            'dns-query',
            'fritzbox-status',
            'ini-util',
            'jabber-send',
            'jabber-daemon',
            'trac-sqlite2mysql',
            'trac-svn2git',
            'trac-manage',
            'trac-git-post-receive-hook',
            'arsoft-backup',
            'arsoft-mailer',
            'edskmgr',
            'alog',
            'onkyo-rs232'
            ],
		data_files=[ 
			('/etc/ldap/schema', ['schema/netconfig.schema']),
			('/etc/cron.hourly', ['cron/update-dhcpd-pxeclients']),
			('/etc/init', ['upstart/jabber-daemon.conf']),
			('/etc', ['config/jabber-daemon.conf']),
			('/etc/arsoft/alog.d', ['config/default_field_alias.conf', 'config/default_log_levels.conf', 
                           'config/default_pattern.conf', 'config/default_shortcuts.conf']),
            ('/etc/edskmgr/hook.d', [ 'edskmgr-support/hooks/arsoft-backup' ]),
			('/etc/nagios-plugins/config', ['nagios/fritzbox.cfg', 
                                   'nagios/openvpn.cfg', 
                                   'nagios/kernel_modules.cfg', 
                                   'nagios/xmpp_notify.cfg', 
                                   'nagios/puppet_agent.cfg', 
                                   'nagios/weather.cfg', 
                                   'nagios/ipp.cfg',
                                   'nagios/rkhunter.cfg',
                                   ]),
            ('/usr/bin', ['onkyo-remote'] ), 
			('/usr/sbin', ['svnbackup', 
                  'cups-admin', 
                  'slapd-config', 
                  'pxeconfig', 
                  'efiinfo', 
                  'nsswitch-config', 'nsswitch-ldap', 'nsswitch-winbind',
                  'autofs-ldap-auth', 
                  'managehosts', 
                  'openvpn-admin', 'openvpn-status',
                  'puppet-setup',
                  'heimdal-password-expire',
                  'dns-update']),
			('/usr/lib/nagios', ['send_xmpp_notification']),
			('/usr/lib/nagios/plugins', ['check_fritzbox', 
                                'check_openvpn', 
                                'check_kernel_modules', 
                                'check_puppet_agent', 
                                'check_weather', 
                                'check_ipp',
                                'check_rkhunter']),
			('/usr/lib/nagios/plugins/test_data', ['test_data/check_ipp.test', 'test_data/check_ipp_jobs.test', 'test_data/check_ipp_completed_jobs.test']),
			('/lib/udev', [ 'edskmgr-support/external-disk' ]),
			('/lib/udev/rules.d', [ 'edskmgr-support/88-external-disk.rules' ]),
			]
		)
