<?php

class CPreseedPluginSsh extends CPreseedPluginBase
{
	private $m_params = array(
		'ssh2_only' => array('preseed' => 'ssh ssh/protocol2_only boolean',
				'value' => 'true',
				'type' => 'boolean'),
		'enabled' => array('preseed' => 'ssh ssh/run_sshd boolean',
				'value' => 'true',
				'type' => 'boolean'),
		'suid_client' => array('preseed' => 'ssh ssh/SUID_client boolean boolean',
				'value' => 'true',
				'type' => 'boolean')
		);

	public function __construct($ldap,$client)
	{
		parent::__construct($ldap,$client);
	}

	public function Initialize()
	{
	}

	public function Deinitialze()
	{
	}

	public function Preseed()
	{
		print "#\n";
		print "# SSH parameters\n";
		print "#\n";

		$this->DefaultPreseed('ssh',$this->m_params);
	}	
	public function ScriptLate()
	{
		return;

		$permit_root_login = $this->ReadString('ssh','permit_root_login','false','boolean');
		$rsa_auth = $this->ReadString('ssh','rsa_auth','true','boolean');
		$pubkey_auth = $this->ReadString('ssh','pubkey_auth','true','boolean');
		$passwd_auth = $this->ReadString('ssh','passwd_auth','false','boolean');
		$krb_auth = $this->ReadString('ssh','krb_auth','false','boolean');
		$callenge_auth = $this->ReadString('ssh','callenge_auth','false','boolean');
		$gssapi_auth = $this->ReadString('ssh','gssapi_auth','true','boolean');
		$gssapi_cleanup = $this->ReadString('ssh','gssapi_cleanup','true','boolean');
		$gssapi_delegate = $this->ReadString('ssh','gssapi_delegate','true','boolean');
		$gssapi_keyexch = $this->ReadString('ssh','gssapi_keyexch','true','boolean');

		$permit_empty_passwd = $this->ReadString('ssh','permit_empty_passwd','false','boolean');
		$use_pam = $this->ReadString('ssh','use_pam','false','boolean');
		$x11_forward = $this->ReadString('ssh','x11_forward','true','boolean');
		$x11_display_offset = $this->ReadString('ssh','x11_display_offset','10','integer');

		$print_motd = $this->ReadString('ssh','print_motd','false','boolean');
		$print_last_log = $this->ReadString('ssh','print_last_log','false','boolean');
		$tcp_keep_alive = $this->ReadString('ssh','tcp_keep_alive','true','boolean');

		$compression = $this->ReadString('ssh','compression','true','boolean');

?>

cat > /etc/ssh/sshd_config <<EOF_SSHD_CONFIG
# Package generated configuration file
# See the sshd(8) manpage for details

# What ports, IPs and protocols we listen for
Port 22
# Use these options to restrict which interfaces/protocols sshd will bind to
#ListenAddress ::
#ListenAddress 0.0.0.0
Protocol 2
# HostKeys for protocol version 2
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_dsa_key
#Privilege Separation is turned on for security
UsePrivilegeSeparation yes
# Lifetime and size of ephemeral version 1 server key
KeyRegenerationInterval 3600
ServerKeyBits 768

# Logging
SyslogFacility AUTH
LogLevel INFO
# Authentication:
LoginGraceTime 120
PermitRootLogin <?php if($permit_root_login=='true') echo "yes\n"; else echo "no\n"; ?>
StrictModes yes

RSAAuthentication <?php if($rsa_auth=='true') echo "yes\n"; else echo "no\n"; ?>
PubkeyAuthentication <?php if($pubkey_auth=='true') echo "yes\n"; else echo "no\n"; ?>
#AuthorizedKeysFile     %h/.ssh/authorized_keys

# Don't read the user's ~/.rhosts and ~/.shosts files
IgnoreRhosts yes
# For this to work you will also need host keys in /etc/ssh_known_hosts
RhostsRSAAuthentication no
# similar for protocol version 2
HostbasedAuthentication no
# Uncomment if you don't trust ~/.ssh/known_hosts for RhostsRSAAuthentication
#IgnoreUserKnownHosts yes

# To enable empty passwords, change to yes (NOT RECOMMENDED)
PermitEmptyPasswords <?php if($permit_empty_passwd=='true') echo "yes\n"; else echo "no\n"; ?>

# Change to yes to enable challenge-response passwords (beware issues with
# some PAM modules and threads)
ChallengeResponseAuthentication <?php if($callenge_auth=='true') echo "yes\n"; else echo "no\n"; ?>

# Change to no to disable tunnelled clear text passwords
PasswordAuthentication <?php if($passwd_auth=='true') echo "yes\n"; else echo "no\n"; ?>

# Kerberos options
KerberosAuthentication <?php if($krb_auth=='true') echo "yes\n"; else echo "no\n"; ?>
#KerberosGetAFSToken no
#KerberosOrLocalPasswd yes
#KerberosTicketCleanup yes

# GSSAPI options
GSSAPIAuthentication <?php if($gssapi_auth=='true') echo "yes\n"; else echo "no\n"; ?>
GSSAPICleanupCredentials <?php if($gssapi_cleanup=='true') echo "yes\n"; else echo "no\n"; ?>
GSSAPIKeyExchange <?php if($gssapi_keyexch=='true') echo "yes\n"; else echo "no\n"; ?>

X11Forwarding <?php if($x11_forward=='true') echo "yes\n"; else echo "no\n"; ?>
X11DisplayOffset <?php echo $x11_display_offset . "\n"; ?>
PrintMotd <?php if($print_motd=='true') echo "yes\n"; else echo "no\n"; ?>
PrintLastLog <?php if($print_last_log=='true') echo "yes\n"; else echo "no\n"; ?>
TCPKeepAlive <?php if($tcp_keep_alive=='true') echo "yes\n"; else echo "no\n"; ?>
#UseLogin no

#MaxStartups 10:30:60
#Banner /etc/issue.net

# Allow client to pass locale environment variables
AcceptEnv LANG LC_*

Subsystem sftp /usr/lib/openssh/sftp-server

UsePAM <?php if($use_pam=='true') echo "yes\n"; else echo "no\n"; ?>
EOF_SSHD_CONFIG

cat > /etc/ssh/ssh_config <<EOF_SSH_CONFIG

# This is the ssh client system-wide configuration file.  See
# ssh_config(5) for more information.  This file provides defaults for
# users, and the values can be changed in per-user configuration files
# or on the command line.

# Configuration data is parsed as follows:
#  1. command line options
#  2. user-specific file
#  3. system-wide file
# Any configuration value is only changed the first time it is set.
# Thus, host-specific definitions should be at the beginning of the
# configuration file, and defaults at the end.

# Site-wide defaults for some commonly used options.  For a comprehensive
# list of available options, their meanings and defaults, please see the
# ssh_config(5) man page.

Host *
#   ForwardAgent no
ForwardX11 <?php if($x11_forward=='true') echo "yes\n"; else echo "no\n"; ?>
#   ForwardX11Trusted yes
#   RhostsRSAAuthentication no
RSAAuthentication <?php if($rsa_auth=='true') echo "yes\n"; else echo "no\n"; ?>
PubkeyAuthentication <?php if($pubkey_auth=='true') echo "yes\n"; else echo "no\n"; ?>
PasswordAuthentication <?php if($passwd_auth=='true') echo "yes\n"; else echo "no\n"; ?>
#   HostbasedAuthentication no
#   BatchMode no
#   CheckHostIP yes
#   AddressFamily any
#   ConnectTimeout 0
#   StrictHostKeyChecking ask
#   IdentityFile ~/.ssh/identity
#   IdentityFile ~/.ssh/id_rsa
#   IdentityFile ~/.ssh/id_dsa
#   Port 22
#   Protocol 2,1
#   Cipher 3des
#   Ciphers aes128-cbc,3des-cbc,blowfish-cbc,cast128-cbc,arcfour,aes192-cbc,aes256-cbc
#   EscapeChar ~
#   Tunnel no
#   TunnelDevice any:any
#   PermitLocalCommand no
SendEnv LANG LC_*
HashKnownHosts yes
GSSAPIAuthentication <?php if($gssapi_auth=='true') echo "yes\n"; else echo "no\n"; ?>
GSSAPIDelegateCredentials <?php if($gssapi_delegate=='true') echo "yes\n"; else echo "no\n"; ?>
Compression  <?php if($compression=='true') echo "yes\n"; else echo "no\n"; ?>

EOF_SSH_CONFIG

<?php
	}

};

?>

