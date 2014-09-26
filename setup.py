#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import sys
import os.path
from distutils.core import setup

source_dir = {2: 'python2', 3: 'python3'}[sys.version_info[0]]

setup(name='arsoft-python',
		version='1.147',
		description='AR Soft Python modules',
		author='Andreas Roth',
		author_email='aroth@arsoft-online.com',
		url='http://www.arsoft-online.com/',
		license='GPLv3',
		platforms=['linux'],
        package_dir={'': source_dir},
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
            os.path.join(source_dir, 'certinfo'),
            os.path.join(source_dir, 'dns-query'),
            os.path.join(source_dir, 'fritzbox-status'),
            os.path.join(source_dir, 'ini-util'),
            os.path.join(source_dir, 'trac-sqlite2mysql'),
            os.path.join(source_dir, 'trac-svn2git'),
            os.path.join(source_dir, 'trac-manage'),
            os.path.join(source_dir, 'trac-git-post-receive-hook'),
            os.path.join(source_dir, 'arsoft-backup'),
            os.path.join(source_dir, 'arsoft-mailer'),
            os.path.join(source_dir, 'edskmgr'),
            os.path.join(source_dir, 'alog'),
            os.path.join(source_dir, 'onkyo-rs232'),
            os.path.join(source_dir, 'system-info'),
            os.path.join(source_dir, 'nsswitch-config'),
            os.path.join(source_dir, 'efiinfo'),
            os.path.join(source_dir, 'ssdp-discover'),
            os.path.join(source_dir, 'managehosts'),
            os.path.join(source_dir, 'openvpn-admin'),
            ],
		data_files=[ 
			('/etc/ldap/schema', ['schema/netconfig.schema']),
			('/etc/cron.hourly', ['cron/update-dhcpd-pxeclients']),
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
            ('/usr/bin', [
                    os.path.join(source_dir, 'onkyo-remote'),
                    os.path.join(source_dir, 'svnbackup'),
                    os.path.join(source_dir, 'cups-admin'),
                    os.path.join(source_dir, 'slapd-config'),
                    os.path.join(source_dir, 'pxeconfig'),
                    os.path.join(source_dir, 'nsswitch-ldap'),
                    os.path.join(source_dir, 'nsswitch-winbind'),
                    os.path.join(source_dir, 'autofs-ldap-auth'),
                    os.path.join(source_dir, 'openvpn-status'),
                    os.path.join(source_dir, 'puppet-setup'),
                    os.path.join(source_dir, 'heimdal-password-expire'),
                    os.path.join(source_dir, 'dns-update')]),
			('/usr/lib/nagios', [os.path.join(source_dir, 'send_xmpp_notification')]),
			('/usr/lib/nagios/plugins', [
                    os.path.join(source_dir, 'check_fritzbox'),
                    os.path.join(source_dir, 'check_openvpn'),
                    os.path.join(source_dir, 'check_kernel_modules'),
                    os.path.join(source_dir, 'check_puppet_agent'),
                    os.path.join(source_dir, 'check_weather'),
                    os.path.join(source_dir, 'check_ipp'),
                    os.path.join(source_dir, 'check_rkhunter'),
             ]),
			('/usr/lib/nagios/plugins/test_data', ['test_data/check_ipp.test', 'test_data/check_ipp_jobs.test', 'test_data/check_ipp_completed_jobs.test']),
			('/lib/udev', [ 'edskmgr-support/external-disk' ]),
			('/lib/udev/rules.d', [ 'edskmgr-support/88-external-disk.rules' ]),
            ('/usr/share/check_mk/checks', [
                'check_mk/checks/apt',
                'check_mk/checks/mysql_slave',
                'check_mk/checks/nginx_cert',
                'check_mk/checks/nginx_status',
                'check_mk/checks/rkhunter',
                'check_mk/checks/openvpn',
                'check_mk/checks/postfix_cert',
                    ] ),
            ('/usr/lib/check_mk_agent/plugins', [
                    'check_mk/plugins/apache_status',
                    'check_mk/plugins/apt',
                    'check_mk/plugins/dmi_sysinfo',
                    'check_mk/plugins/dmraid',
                    'check_mk/plugins/mk_mysql',
                    'check_mk/plugins/mk_postgres',
                    'check_mk/plugins/nfsexports',
                    'check_mk/plugins/nginx_cert',
                    'check_mk/plugins/nginx_status',
                    'check_mk/plugins/smart',
                    'check_mk/plugins/rkhunter',
                    'check_mk/plugins/openvpn',
                    'check_mk/plugins/postfix_cert',
                ] )
            ]
		)
