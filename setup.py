#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import sys
import platform
import os.path
from distutils.core import setup

source_dir = {2: 'python2', 3: 'python3'}[sys.version_info[0]]
is_python2 = True if sys.version_info[0] == 2 else False
is_python3 = True if sys.version_info[0] == 3 else False
target_distribution = os.environ.get('TARGET_DISTRIBUTION', 'unknown')

def version_dep_scripts(scripts, prefix=None):
    ret = []
    for (s, v) in scripts:
        if sys.version_info[0] == v or v is None:
            if prefix is None:
                ret.append(os.path.join(source_dir, s))
            else:
                ret.append(os.path.join(prefix, source_dir, s))
    return ret

def distribution_dep_scripts(scripts, prefix=None):
    ret = []
    sys.stderr.write('distribution_dep_scripts dd=%s\n' % target_distribution)
    for (s, d) in scripts:
        if target_distribution in d or d is None:
            if prefix is None:
                ret.append(s)
            else:
                ret.append(os.path.join(prefix, s))
    return ret

setup(name='arsoft-python',
		version='1.246',
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
                    'arsoft.eurosport',
                    'arsoft.fritzbox', 
                    'arsoft.kerberos',
                    'arsoft.git',
                    'arsoft.ldap',
                    'arsoft.ldap.slapd',
                    'arsoft.m3u8',
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
		scripts=version_dep_scripts([
            ('certinfo', 3),
            ('dns-query', 3),
            ('fritzbox-status', 3),
            ('ini-util', 3),
            ('trac-sqlite2mysql', 2),
            ('trac-svn2git', 2),
            ('trac-manage', 2),
            ('trac-git-post-receive-hook', 2),
            ('arsoft-backup', 3),
            ('arsoft-mailer', 3),
            ('edskmgr', 3),
            ('alog', 3),
            ('onkyo-rs232', 3),
            ('system-info', 3),
            ('nsswitch-config', 3),
            ('efiinfo', 3),
            ('ssdp-discover', 3),
            ('managehosts', 3),
            ('openvpn-admin', 3),
            ('svnbackup', 3),
            ('cups-admin', 3),
            ('slapd-config', 3),
            ('autofs-ldap-auth', 3),
            ('puppet-setup', 3),
            ('puppet-template-check', 3),
            ('heimdal-password-expire', 2),
            ('dns-update', 3),
            ('eurosport-stream', 3),
            ]),
		data_files=[ 
			('/etc/ldap/schema', ['schema/netconfig.schema']),
			('/etc/cron.hourly', ['cron/update-dhcpd-pxeclients'] +
                         distribution_dep_scripts([
                             ('check_mk/cron/python2/check_mk_agent_apt', ['precise', 'trusty']),
                             ('check_mk/cron/python3/check_mk_agent_apt', ['wily', 'xenial']),
                             ] )  ),
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
                    os.path.join(source_dir, 'nsswitch-ldap'),
                    os.path.join(source_dir, 'nsswitch-winbind'),
                    os.path.join(source_dir, 'nsswitch-sss'),
                    os.path.join(source_dir, 'openvpn-status'),
                    ]),
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
                'check_mk/checks/nginx_cert',
                'check_mk/checks/rkhunter',
                'check_mk/checks/openvpn',
                'check_mk/checks/postfix_cert',
                'check_mk/checks/samba_status',
                'check_mk/checks/puppet_agent',
                'check_mk/checks/puppetdb',
                'check_mk/checks/openvz_ubc',
                'check_mk/checks/jenkins',
                'check_mk/checks/slapd_cert',
                'check_mk/checks/eiscp',
                'check_mk/checks/cyrus_imapd',
                'check_mk/checks/fritz_ddns',
                'check_mk/checks/systemd',
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
                    'check_mk/plugins/samba_status',
                    'check_mk/plugins/puppet_agent',
                    'check_mk/plugins/puppetdb',
                    'check_mk/plugins/openvz_ubc',
                    'check_mk/plugins/jenkins',
                    'check_mk/plugins/slapd_cert',
                    'check_mk/plugins/cyrus_imapd',
                ] ),
            ('/usr/share/check_mk/special', [
                    'check_mk/special_agent/agent_fritzbox',
                    'check_mk/special_agent/agent_eiscp'
                ] )
            ]
		)
