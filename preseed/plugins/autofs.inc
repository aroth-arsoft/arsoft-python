<?php

class CPreseedPluginAutofs extends CPreseedPluginBase
{
	private $m_params = array();

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
	}	
	public function ScriptLate()
	{
		global $config;
		print "#\n";
		print "# AutoFS setup\n";
		print "#\n";
		
		return;

		# cn=base,ou=default,ou=autofs,ou=preseed,ou=config,dc=arsoft,dc=homeip,dc=net,o=arsoft
		# cn=base,ou=default,ou=autofs,ou=preseed,ou=config,dc=arsoft,dc=homeip,dc=net,o=arsoft
		$base = $this->ReadString('autofs','base',$config['ldap']['base'],'string');
		$timeout = $this->ReadString('autofs','timeout',300,'integer');

?>
cat > /etc/default/autofs <<EOF_AUTOFS
# Timeout value in seconds (default: 300)
TIMEOUT=<?php echo $timeout; ?>

# Direct maps are only partially implemented 
# and could silently break things. See /usr/share/doc/autofs/README.direct for information
# about current limitations and check your configurations before enabling them.
DISABLE_DIRECT=1

# The LDAP URI for auto.master
# (e. g. LDAPURI="ldap://ldapserver.example.com/")
LDAPURI=<?php echo 'ldap://' . $config['ldap']['server']; ?>

# The LDAP base for auto.master
# (e. g. LDAPBASE="ou=auto.master,ou=Automount,dc=example,dc=com")
LDAPBASE=<?php echo $base; ?>

# Restart autofs automatically on upgrades -- normally, you want this, but
# if you have critical files on autofs-mounted directories (the new autofs
# .deb file, for instance), you may want to set this to 1
#AUTOFS_DONT_RESTART_ON_UPGRADES=
EOF_AUTOFS

# Remove the autofs daemon from init.d
#update-rc.d -f autofs remove

## And put in a script which reloads the autofs daemon on nic change
#cat > /etc/network/if-up.d/autofs <<EOF_IF_UP_AUTOFS
##!/bin/sh
## Not for loopback!
#[ "\$IFACE" != "lo" ] || exit 0
#/etc/init.d/autofs reload
#EOF_IF_UP_AUTOFS
#chmod +x /etc/network/if-up.d/autofs

#cat > /etc/network/if-down.d/autofs <<EOF_IF_DOWN_AUTOFS
##!/bin/sh
## Not for loopback!
#[ "\$IFACE" != "lo" ] || exit 0
#/etc/init.d/autofs stop
#EOF_IF_DOWN_AUTOFS
#chmod +x /etc/network/if-down.d/autofs



#AUTOFS_NN=28
#for f in `ls -1 /etc/rc?.d/S??autofs 2>/dev/null`; do
#    file=`basename "\$f"`
#    target=`echo -n "\$f" | sed "s@\$file@S\${AUTOFS_NN}autofs@"`
#    if [ ! "\$f" = "\$target" ]; then
#        echo "move \$f \$target"
#        mv \$f \$target
#    fi
#done
#for f in `ls -1 /etc/rc?.d/K??autofs 2>/dev/null`; do
#    file=`basename "\$f"`
#    target=`echo -n "\$f" | sed "s@\$file@K\${AUTOFS_NN}autofs@"`
#    if [ ! "\$f" = "\$target" ]; then
#        echo "move \$f \$target"
#        mv \$f \$target
#    fi
#done

<?php
	}
};

?>

