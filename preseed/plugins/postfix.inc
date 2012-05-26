<?php

class CPreseedPluginPostfix extends CPreseedPluginBase
{
	private $m_params = array();

	public function __construct($ldap,$client)
	{
		parent::__construct($ldap,$client);
	}

	public function Initialize()
	{
		global $config;
/*
postfix postfix/master_upgrade_warning  boolean
postfix postfix/db_upgrade_warning      boolean true
postfix postfix/mailname        string  /etc/mailname
postfix postfix/tlsmgr_upgrade_warning  boolean
postfix postfix/recipient_delim string  +
postfix postfix/dynamicmaps_upgrade_warning     boolean
postfix postfix/main_mailer_type        select  No configuration
postfix postfix/transport_map_warning   note
postfix postfix/relayhost       string
postfix postfix/procmail        boolean
postfix postfix/bad_recipient_delimiter note
postfix postfix/chattr  boolean false
postfix postfix/root_address    string
postfix postfix/rfc1035_violation       boolean false
postfix postfix/mydomain_warning        boolean
postfix postfix/mynetworks      string  127.0.0.0/8
postfix postfix/destinations    string
postfix postfix/nqmgr_upgrade_warning   boolean
postfix postfix/not_configured  note
postfix postfix/mailbox_limit   string  0
postfix postfix/protocols       select
*/

		$this->m_params = array(
		'upgrade_warning' => array('preseed' => 'd-i postfix/master_upgrade_warning note',
				'value' => '',
				'type' => 'note'),
		'db_upgrade_warning' => array('preseed' => 'd-i postfix/db_upgrade_warning boolean',
				'value' => 'false',
				'type' => 'boolean'),
		'dynamicmaps_upgrade_warning' => array('preseed' => 'd-i postfix/dynamicmaps_upgrade_warning note',
				'value' => '',
				'type' => 'note'),
		'mailname' => array('preseed' => 'd-i postfix/mailname string',
				'value' => 'mail.arsoft.homeip.net',
				'type' => 'string'),
		'configtype' => array('preseed' => 'd-i postfix/main_mailer_type select',
				'value' => 'No configuration',
				'type' => 'string'),
		'libc_maildir' => array('preseed' => 'libc-client2002edebian libc-client/no_maildir_warning boolean',
				'value' => 'true',
				'type' => 'boolean')
		);
	}

	public function Deinitialze()
	{
	}

	public function Preseed()
	{
		print "#\n";
		print "# Postfix parameters\n";
		print "#\n";

		$this->DefaultPreseed('postfix',$this->m_params);
	}	
	public function ScriptLate()
	{
		global $config;
		print "#\n";
		print "# Postfix/fetchmail setup\n";
		print "#\n";
		
		return;
		

		$start_fetchmail = $this->ReadString('postfix','fetchmail_start','yes','string');
		$start_saslauthd = $this->ReadString('postfix','saslauthd_start','yes','string');
		$start_spamassassin = $this->ReadString('postfix','spamassassin_start','yes','string');
		if($start_spamassassin == 'yes')
			$start_spamassassin = '1';
		else
			$start_spamassassin = '0';

		$aliases = $this->ReadString('postfix','aliases','','array');

		if(is_array($aliases))
		{
			foreach($aliases as $alias)
			{
				print "grep \"$alias\" /etc/aliases 2>&1 > /dev/null\n";
				print "if [ $? -ne 0 ]; then echo \"$alias\" >> /etc/aliases; newaliases; fi\n";
			}
		}

?>
if [ -f /etc/default/fetchmail ]; then
cat > /etc/default/fetchmail <<EOF_FETCHMAIL
# This file will be used to declare some vars for fetchmail
#
# Uncomment the following if you dont want localized log messages
# export LC_ALL=C

# Declare here if we want to start fetchmail. 'yes' or 'no'
START_DAEMON=<?php echo $start_fetchmail; ?>

EOF_FETCHMAIL
echo "Configured fetchmail to start at boot"

fi

if [ -f /etc/default/saslauthd ]; then
cat > /etc/default/saslauthd <<EOF_SASLAUTHD
#
# Settings for saslauthd daemon
#

# Should saslauthd run automatically on startup? (default: no)
START=<?php echo $start_saslauthd; ?>

# Which authentication mechanisms should saslauthd use? (default: pam)
#
# Available options in this Debian package:
# getpwent  -- use the getpwent() library function
# kerberos5 -- use Kerberos 5
# pam       -- use PAM
# rimap     -- use a remote IMAP server
# shadow    -- use the local shadow password file
# sasldb    -- use the local sasldb database file
# ldap      -- use LDAP (configuration is in /etc/saslauthd.conf)
#
# Only one option may be used at a time. See the saslauthd man page
# for more information.
#
# Example: MECHANISMS="pam"
MECHANISMS="pam"

# Additional options for this mechanism. (default: none)
# See the saslauthd man page for information about mech-specific options.
MECH_OPTIONS=""

# How many saslauthd processes should we run? (default: 5)
# A value of 0 will fork a new process for each connection.
THREADS=5

# Other options (default: -c)
# See the saslauthd man page for information about these options.
#
# Example for postfix users: "-c -m /var/spool/postfix/var/run/saslauthd"
# Note: See /usr/share/doc/sasl2-bin/README.Debian
OPTIONS="-c"
EOF_SASLAUTHD

echo "Configured saslauthd to start at boot"
fi

if [ -f /etc/default/spamassassin ]; then
cat > /etc/default/spamassassin <<EOF_SPAMASSASSIN
# /etc/default/spamassassin
# Duncan Findlay

# WARNING: please read README.spamd before using.
# There may be security risks.

# Change to one to enable spamd
ENABLED=<?php echo $start_spamassassin; ?>

# Options
# See man spamd for possible options. The -d option is automatically added.

# SpamAssassin uses a preforking model, so be careful! You need to
# make sure --max-children is not set to anything higher than 5,
# unless you know what you're doing.

OPTIONS="--create-prefs --max-children 5 --helper-home-dir"

# Pid file
# Where should spamd write its PID to file? If you use the -u or
# --username option above, this needs to be writable by that user.
# Otherwise, the init script will not be able to shut spamd down.
PIDFILE="/var/run/spamd.pid"

# Set nice level of spamd
#NICE="--nicelevel 15"
EOF_SPAMASSASSIN
fi

<?php
	}
};

?>

