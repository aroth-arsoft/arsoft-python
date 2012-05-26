<?php

class CPreseedPluginLdap extends CPreseedPluginBase
{
	private $m_params = array();

	public function __construct($ldap,$client)
	{
		parent::__construct($ldap,$client);
	}

	public function Initialize()
	{
		global $config;

		$this->m_params = array(
		'rootbinddn' => array('preseed' => array('libpam-ldap libpam-ldap/rootbinddn string',
							'libnss-ldap libnss-ldap/rootbinddn string',
                            'ldap-auth-config ldap-auth-config/rootbinddn string'),
				'value' => 'cn=Manager,o=arsoft',
				'type' => 'string'),
		'rootbindpw' => array('preseed' => array('libpam-ldap libpam-ldap/rootbindpw password',
							'libnss-ldap libnss-ldap/rootbindpw  password',
                            'ldap-auth-config ldap-auth-config/rootbindpw password'),
				'value' => '',
				'type' => 'string'),
		'binddn' => array('preseed' => array('libpam-ldap libpam-ldap/binddn string',
							'libnss-ldap libnss-ldap/binddn string',
                            'ldap-auth-config ldap-auth-config/binddn string'),
				'value' => '',
				'type' => 'string'),
		'bindpw' => array('preseed' => array('libpam-ldap libpam-ldap/bindpw password',
							'libnss-ldap libnss-ldap/bindpw password',
                            'ldap-auth-config ldap-auth-config/bindpw password'),
				'value' => '',
				'type' => 'string'),
		'basedn' => array('preseed' => array('libpam-ldap shared/ldapns/base-dn string',
							'libnss-ldap shared/ldapns/base-dn string',
                            'ldap-auth-config ldap-auth-config/ldapns/base-dn string'),
				'value' => 'o=arsoft',
				'type' => 'string'),
		'override' => array('preseed' => array('libpam-ldap libpam-ldap/override boolean',
							'libnss-ldap libnss-ldap/override boolean',
                            'ldap-auth-config ldap-auth-config/override boolean'),
				'value' => 'true',
				'type' => 'boolean'),
		'enable_login' => array('preseed' => array('libpam-ldap libpam-ldap/dblogin boolean',
								'libnss-ldap libnss-ldap/dblogin boolean',
                                'ldap-auth-config ldap-auth-config/dblogin boolean'),
				'value' => 'true',
				'type' => 'boolean'),
		'enable_root_login' => array('preseed' => array('libpam-ldap libpam-ldap/dbrootlogin boolean',
								'libnss-ldap libnss-ldap/dbrootlogin boolean',
                                'ldap-auth-config ldap-auth-config/dbrootlogin boolean'),
				'value' => 'true',
				'type' => 'boolean'),
		'version' => array('preseed' => array('libpam-ldap shared/ldapns/ldap_version select',
							'libnss-ldap shared/ldapns/ldap_version select'),
				'value' => '3',
				'type' => 'integer'),
		'server' => array('preseed' => array('libpam-ldap shared/ldapns/ldap-server string',
							'libnss-ldap shared/ldapns/ldap-server string',
                            'ldap-auth-config ldap-auth-config/ldapns/ldap-server string'),
				'value' => $config['ldap']['server'],
				'type' => 'string'),
		'pam_password' => array('preseed' => array('libpam-ldap libpam-ldap/pam_password select',
                                                    'ldap-auth-config ldap-auth-config/pam_password select'),
				'value' => 'exop',
				'type' => 'string'),
		'nsswitch' => array('preseed' => 'libnss-ldap libnss-ldap/nsswitch note',
				'value' => '',
				'type' => 'string'),
		'server_passwd' => array('preseed' => array('slapd slapd/password2 password',
							'slapd slapd/password1 password'),
				'value' => 'secret',
				'type' => 'string'),
		'allow_v2' => array('preseed' => 'slapd slapd/allow_ldap_v2 boolean',
				'value' => 'true',
				'type' => 'boolean'),
		'version' => array('preseed' => 'ldap-auth-config ldap-auth-config/ldapns/ldap_version select',
				'value' => '3',
				'type' => 'integer'),
		'kerberos_read_conf' => array('preseed' => 'krb5-config     krb5-config/read_conf   boolean',
				'value' => 'true',
				'type' => 'boolean'),
		'kerberos_dns' => array('preseed' => 'krb5-config     krb5-config/dns_for_default     boolean',
				'value' => 'false',
				'type' => 'boolean'),
		'kerberos_admin' => array('preseed' => 'krb5-config     krb5-config/admin_server        string',
				'value' => 'kerberos.arsoft.homeip.net',
				'type' => 'string'),
		'kerberos_kdc' => array('preseed' => 'krb5-config     krb5-config/kerberos_servers        string',
				'value' => 'kerberos.arsoft.homeip.net',
				'type' => 'string'),
		'kerberos_realm' => array('preseed' => 'krb5-config     krb5-config/default_realm       string',
				'value' => 'ARSOFT.HOMEIP.NET',
				'type' => 'string')

        );


/*

slapd   slapd/internal/adminpw  password

slapd   slapd/password_mismatch note
slapd   slapd/fix_directory     boolean true
slapd   slapd/invalid_config    boolean true
slapd   shared/organization     string  arsoft.homeip.net
slapd   slapd/upgrade_slapcat_failure   note
slapd   slapd/upgrade_slapadd_failure   note
slapd   slapd/backend   select  BDB
slapd   slapd/dump_database     select  when needed
slapd   slapd/no_configuration  boolean false
slapd   slapd/migrate_ldbm_to_bdb       boolean true
slapd   slapd/move_old_database boolean true
slapd   slapd/suffix_change     boolean false
slapd   slapd/slave_databases_require_updateref note
slapd   slapd/dump_database_destdir     string  /var/backups/slapd-VERSION
slapd   slapd/autoconf_modules  boolean true
# Do you want your database to be removed when slapd is purged?
slapd   slapd/purge_database    boolean false
slapd   slapd/domain    string  arsoft.homeip.net

ldap-auth-config        ldap-auth-config/rootbindpw     password
ldap-auth-config        ldap-auth-config/rootbinddn     string  cn=manager,dc=example,dc=net
ldap-auth-config        ldap-auth-config/bindpw password
ldap-auth-config        ldap-auth-config/binddn string  cn=proxyuser,dc=example,dc=net
ldap-auth-config        ldap-auth-config/ldapns/base-dn string  dc=example,dc=net
ldap-auth-config        ldap-auth-config/override       boolean true
ldap-auth-config        ldap-auth-config/pam_password   select  md5
ldap-auth-config        ldap-auth-config/ldapns/ldap-server     string  ldapi:///
ldap-auth-config        ldap-auth-config/ldapns/ldap_version    select  3
ldap-auth-config        ldap-auth-config/dbrootlogin    boolean true
ldap-auth-config        ldap-auth-config/dblogin        boolean false


ldap-auth-config        ldap-auth-config/move-to-debconf        boolean true

*/
		
	}

	public function Deinitialze()
	{
	}

	public function Preseed()
	{
		print "#\n";
		print "# LDAP parameters\n";
		print "#\n";

		$this->DefaultPreseed('ldap',$this->m_params);
	}	
	public function ScriptLate()
	{
		global $config;
		print "#\n";
		print "# LDAP setup\n";
		print "#\n";

		return;
?>


grep 'preseed/plugins/ldap.inc' /etc/ldap/ldap.conf 2>&1 > /dev/null
if [ $? -ne 0 ]; then
cat > /etc/ldap/ldap.conf <<EOF_OPENLDAP_CONF
# $OpenLDAP: pkg/ldap/libraries/libldap/ldap.conf,v 1.9 2000/09/04 19:57:01 kurt Exp $
#
# LDAP Defaults
#

# See ldap.conf(5) for details
# This file should be world readable but not world writable.

SASL_SECPROPS   noanonymous

BASE    o=arsoft

HOST    ldap.arsoft.homeip.net

TLS_CACERT      /etc/arsoft/certs/root.crt
TLS_REQCERT    demand
#TLS_CIPHER_SUITE HIGH:MEDIUM:+SSLV3

SUDOERS_DEBUG   0
SUDOERS_BASE    ou=Sudoers,ou=Authentication,o=arsoft

#SIZELIMIT      12
#TIMELIMIT      15
#DEREF          never

EOF_OPENLDAP_CONF
echo "adjustments to ldap.conf complete"
fi

PAM_LDAP_CONF=''
if [ -e /etc/ldap.conf ]; then
	PAM_LDAP_CONF='/etc/ldap.conf'
	LIBNSS_LDAP_CONF='/etc/ldap.conf'
else
	PAM_LDAP_CONF='/etc/pam_ldap.conf'
	LIBNSS_LDAP_CONF='/etc/libnss-ldap.conf'
fi

grep 'preseed/plugins/ldap.inc' $LIBNSS_LDAP_CONF 2>&1 > /dev/null
if [ $? -ne 0 ]; then
cat >> $LIBNSS_LDAP_CONF <<EOF_LIBNSS_LDAP_CONF
# preseed/plugins/ldap.inc 
# AR Soft specific LDAP configuration
nss_base_passwd ou=Users,ou=Authentication,o=arsoft
nss_base_shadow ou=Authentication,o=arsoft
nss_base_group  ou=Groups,ou=Authentication,o=arsoft

# reconnect for nss
nss_reconnect_tries 1
nss_reconnect_sleeptime 1
nss_reconnect_maxsleeptime 8
nss_reconnect_maxconntries 2

ssl start_tls
tls_cacertfile /etc/arsoft/certs/root.crt
tls_checkpeer yes

# debug settings
#debug 511
#logdir /var/log

EOF_LIBNSS_LDAP_CONF
echo "adjustments to $LIBNSS_LDAP_CONF complete"
fi

grep 'preseed/plugins/ldap.inc' $PAM_LDAP_CONF 2>&1 > /dev/null
if [ $? -ne 0 ]; then
cat >> $PAM_LDAP_CONF <<EOF_PAM_LDAP_CONF
# preseed/plugins/ldap.inc 
# AR Soft specific LDAP configuration
nss_base_passwd ou=Users,ou=Authentication,o=arsoft
nss_base_shadow ou=Authentication,o=arsoft
nss_base_group  ou=Groups,ou=Authentication,o=arsoft
nss_base_aliases  ou=Aliases,ou=Authentication,o=arsoft

# reconnect for nss
nss_reconnect_tries 1
nss_reconnect_sleeptime 1
nss_reconnect_maxsleeptime 8
nss_reconnect_maxconntries 2

ssl start_tls
tls_cacertfile /etc/arsoft/certs/root.crt
tls_checkpeer yes

# debug settings
#debug 511
#logdir /var/log

EOF_PAM_LDAP_CONF
echo "adjustments to $PAM_LDAP_CONF complete"
fi

#grep 'pam_ldap.so' /etc/pam.d/common-account 2>&1 > /dev/null
#if [ $? -ne 0 ]; then
#cat /etc/pam.d/common-account | sed 's@^account.*required.*pam_unix.so@account sufficient pam_ldap.so\
#account required pam_unix.so@' > /tmp/common-account
#cp /tmp/common-account /etc/pam.d/common-account
#echo "Patched common-account"
#fi

#grep 'pam_ldap.so' /etc/pam.d/common-auth 2>&1 > /dev/null
#if [ $? -ne 0 ]; then
#cat /etc/pam.d/common-auth | sed 's@^auth.*req.*pam_unix.so@auth sufficient pam_ldap.so\
#auth required pam_unix.so nullok_secure try_first_pass@' > /tmp/common-auth
#cp /tmp/common-auth /etc/pam.d/common-auth
#echo "Patched common-auth"
#fi

#grep 'pam_ldap.so' /etc/pam.d/common-password 2>&1 > /dev/null
#if [ $? -ne 0 ]; then
#cat /etc/pam.d/common-password | sed 's@^password.*required.*pam_unix.so.*md5$@password sufficient pam_ldap.so md5\
#password required pam_unix.so nullok obscure min=4 max=8 md5 try_first_pass@' > /tmp/common-password
#cp /tmp/common-password /etc/pam.d/common-password
#echo "Patched common-password"
#fi

#grep 'pam_ldap.so' /etc/pam.d/common-session 2>&1 > /dev/null
#if [ $? -ne 0 ]; then
#cat /etc/pam.d/common-session | sed 's@^session.*required.*pam_unix.so@session sufficient pam_ldap.so\
#session required pam_unix.so@' > /tmp/common-session
#cp /tmp/common-session /etc/pam.d/common-session
#echo "Patched common-session"
#fi


cat > /etc/pam.d/common-account <<EOF_COMMON_ACCOUNT
#
# /etc/pam.d/common-account - authorization settings common to all services
#
# This file is included from other service-specific PAM config files,
# and should contain a list of the authorization modules that define
# the central access policy for use on the system.  The default is to
# only deny service to users whose accounts are expired in /etc/shadow.
#
#account sufficient pam_ldap.so 
account sufficient pam_krb5.so
account required pam_unix.so
EOF_COMMON_ACCOUNT

cat > /etc/pam.d/common-auth <<EOF_COMMON_AUTH
#
# /etc/pam.d/common-auth - authentication settings common to all services
#
# This file is included from other service-specific PAM config files,
# and should contain a list of the authentication modules that define
# the central authentication scheme for use on the system
# (e.g., /etc/shadow, LDAP, Kerberos, etc.).  The default is to use the
# traditional Unix authentication mechanisms.
#
#auth sufficient pam_ldap.so 
auth required pam_env.so
auth sufficient pam_unix.so try_first_pass likeauth nullok
auth sufficient pam_krb5.so try_first_pass
auth required pam_deny.so
#auth requisite pam_unix.so nullok_secure try_first_pass
#auth    optional    pam_smbpass.so migrate
EOF_COMMON_AUTH

cat > /etc/pam.d/common-password <<EOF_COMMON_PASSWORD
#
# /etc/pam.d/common-password - password-related modules common to all services
#
# This file is included from other service-specific PAM config files,
# and should contain a list of modules that define  the services to be
#used to change user passwords.  The default is pam_unix

# The "nullok" option allows users to change an empty password, else
# empty passwords are treated as locked accounts.
#
# (Add md5 after the module name to enable MD5 passwords)
#
# The "obscure" option replaces the old OBSCURE_CHECKS_ENAB option in
# login.defs. Also the "min" and "max" options enforce the length of the
# new password.

password   required     pam_cracklib.so difok=2 minlen=8 dcredit=2 ocredit=2 retry=3 
password   sufficient   pam_unix.so try_first_pass use_authtok nullok md5 shadow 
password   sufficient   pam_krb5.so try_first_pass use_authtok 
password   required     pam_deny.so 
 

#password sufficient pam_krb5.so use_first_pass use_authtok clear_on_fail
#password sufficient pam_ldap.so md5 try_first_pass
#password required pam_unix.so nullok obscure min=4 max=8 md5 try_first_pass use_authtok
#password sufficient pam_unix.so nullok obscure min=4 max=8 md5 try_first_pass
#password required pam_deny.so

# Alternate strength checking for password. Note that this
# requires the libpam-cracklib package to be installed.
# You will need to comment out the password line above and
# uncomment the next two in order to use this.
# (Replaces the OBSCURE_CHECKS_ENAB, CRACKLIB_DICTPATH)
#
# password required       pam_cracklib.so retry=3 minlen=6 difok=3
# password required       pam_unix.so use_authtok nullok md5
EOF_COMMON_PASSWORD

cat > /etc/pam.d/common-session <<EOF_COMMON_SESSION
#
# /etc/pam.d/common-session - session-related modules common to all services
#
# This file is included from other service-specific PAM config files,
# and should contain a list of modules that define tasks to be performed
# at the start and end of sessions of *any* kind (both interactive and
# non-interactive).  The default is pam_unix.
#
#session sufficient pam_ldap.so 
session required pam_limits.so
session required pam_unix.so
session optional pam_krb5.so
#session optional pam_foreground.so 
EOF_COMMON_SESSION


cat > /etc/krb5.conf <<EOF_KRB5_CONF
[libdefaults]
    default_realm = ARSOFT.HOMEIP.NET
    ticket_lifetime = 600
#       default_etypes = des3-hmac-sha1 des-cbc-crc des-cbc-md5
#   default_etypes_des = des3-hmac-sha1 des-cbc-crc des-cbc-md5
    default_etypes = des-cbc-crc
    default_etypes_des = des-cbc-crc
    default_tgs_enctypes = des-cbc-crc
    default_tkt_enctypes = des-cbc-crc



# The following krb5.conf variables are only for MIT Kerberos.
	krb4_config = /etc/krb.conf
	krb4_realms = /etc/krb.realms
	kdc_timesync = 1
	ccache_type = 4
	forwardable = true
	proxiable = true

# The following encryption type specification will be used by MIT Kerberos
# if uncommented.  In general, the defaults in the MIT Kerberos code are
# correct and overriding these specifications only serves to disable new
# encryption types as they are added, creating interoperability problems.

#	default_tgs_enctypes = aes256-cts arcfour-hmac-md5 des3-hmac-sha1 des-cbc-crc des-cbc-md5
#	default_tkt_enctypes = aes256-cts arcfour-hmac-md5 des3-hmac-sha1 des-cbc-crc des-cbc-md5
#	permitted_enctypes = aes256-cts arcfour-hmac-md5 des3-hmac-sha1 des-cbc-crc des-cbc-md5

# The following libdefaults parameters are only for Heimdal Kerberos.
	v4_instance_resolve = false
	v4_name_convert = {
		host = {
			rcmd = host
			ftp = ftp
		}
		plain = {
			something = something-else
		}
	}
	fcc-mit-ticketflags = true

[kdc]
    database = {
        realm = ARSOFT.HOMEIP.NET
        dbname = ldap:ou=kerberos,ou=Authentication,o=arsoft
#	dbname = ldap:o=arsoft
        mkey_file = /var/lib/heimdal-kdc/m-key
        log_file = /var/lib/heimdal-kdc/db.log
        acl_file = /var/lib/heimdal-kdc/kdc.acl
    }


[realms]
	ARSOFT.HOMEIP.NET = {
		kdc = kerberos.arsoft.homeip.net
		kadmin = kerberos.arsoft.homeip.net
	}

[domain_realm]
	arsoft.homeip.net = ARSOFT.HOMEIP.NET
	.arsoft.homeip.net = ARSOFT.HOMEIP.NET

[logging]
        kdc = FILE:/var/log/heimdal/kdc.log
 #       kdc = 1-/SYSLOG:DEBUG
        kadmind = FILE:/var/log/heimdal/kadmin.log
        kpasswdd = FILE:/var/log/heimdal/kpasswdd.log
        default = FILE:/var/log/heimdal/default.log

[appdefaults]
 pam = {
   debug = false
   ticket_lifetime = 36000
   renew_lifetime = 36000
   forwardable = true
   krb4_convert = false
 }
 kinit = {
   ticket_lifetime = 36000
   renew_lifetime = 36000
   forwardable = true
 }

[ktutil]
	kdc = kerberos.arsoft.homeip.net
EOF_KRB5_CONF

#cat > /etc/default/avahi-daemon <<EOF_AVAHI
## 0 = don't start, 1 = start
#AVAHI_DAEMON_START=0
#
#EOF_AVAHI

cat /etc/nsswitch.conf | \
	sed 's@^passwd\:.*@passwd\:          files ldap@' | \
	sed 's@^group\:.*@group\:          files ldap@' | \
	sed 's@^shadow\:.*@shadow\:          files ldap@' | \
	sed 's@^automount\:.*@automount\:       ldap@' | \
	cat > /tmp/nsswitch.conf
has_automount=`grep automount /tmp/nsswitch.conf`
if [ -z "$has_automount" ]; then
	echo "automount:             ldap" >> /tmp/nsswitch.conf
fi
has_aliases=`grep aliases /tmp/nsswitch.conf`
if [ -z "$has_aliases" ]; then
	echo "aliases:             files ldap" >> /tmp/nsswitch.conf
fi
cp /tmp/nsswitch.conf /etc/nsswitch.conf
echo "adjustments to nsswitch.conf complete"
if [ -f /etc/init.d/nscd ]; then
	/etc/init.d/nscd force-reload
	echo "reload nscd"
else
	echo "nscd not reloaded, since not present"
fi

group_file_mod() {
groupline=`grep $1 /etc/group`
is_in_group=`echo $groupline | cut -d: -f 4 | grep $2`

if [ -z "$is_in_group" ]; then
	echo "Add user $2 to group $1"
	if [ ! -z "$groupline" ]; then
	    members=`echo $groupline | cut -d: -f 4`
    	if [ -z "$members" ]; then
        	newgroupline="${groupline}${2}"
	    else
    	    newgroupline="${groupline},${2}"
	    fi

	#    echo "old group line $groupline"
	#    echo "new group line $newgroupline"
    	cat /etc/group | sed "s@$groupline@$newgroupline@" > /tmp/group && cp /tmp/group /etc/group
	fi
fi
}

domainUsers=`getent group domainUsers | cut -d: -f 4 | sed 's@,@ @g'`

for user in $domainUsers; do
	group_file_mod users $user
	group_file_mod cdrom $user
	group_file_mod floppy $user
	group_file_mod video $user
	group_file_mod audio $user
	group_file_mod plugdev $user
	group_file_mod dialout $user
	group_file_mod lpadmin $user
	group_file_mod scanner $user
done


<?php
	}

};

?>

