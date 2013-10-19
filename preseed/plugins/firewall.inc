<?php

class CPreseedPluginFirewall extends CPreseedPluginBase
{
	private $m_params = array();

	public function __construct($ldap,$client)
	{
		parent::__construct($ldap,$client);
	}

	public function Initialize()
	{
		global $config;

	}

	public function Deinitialze()
	{
	}

	public function ScriptLate()
	{
		global $config;
		print "#\n";
		print "# Firewall setup\n";
		print "#\n";

		return;
		
		$enable = $this->ReadString('firewall','enable','true','boolean');
		
		$firewall_rules_url = $this->ReadString('firewall','rules','','string');

		if(empty($firewall_rules_url))
			$enable = false;
?>

FIREWALL_ENABLE=<?php if($enable) print "1\n"; else print "0\n";  ?>
FIREWALL_RULES_URL=<?php echo $firewall_rules_url; print "\n";  ?>
FIREWALL_RULES_FILE=`echo -n "/etc/firewall/"; basename "$FIREWALL_RULES_URL"`

if [ ! -d '/etc/firewall' ]; then
	mkdir /etc/firewall 2>&1 > /dev/null
fi

if [ ! -z "$FIREWALL_RULES_URL" ]; then
download_file $FIREWALL_RULES_URL $FIREWALL_RULES_FILE
RES=$?
if [ $RES -eq 0 ]; then
	echo "Firewall rules downloaded and installed"
else
	echo "Failed to download and install firewall rules from $FIREWALL_RULES_URL"
	FIREWALL_ENABLE=0
fi
fi

grep 'preseed/plugins/firewall.inc' /etc/init.d/firewall 2>&1 > /dev/null
if [ $? -ne 0 ]; then
cat >> /etc/init.d/firewall <<EOF_FIREWALL_INIT_D_SCRIPT
#!/bin/bash
# preseed/plugins/firewall.inc
RETVAL=0

disable_firewall() {
#
# Set the default policy
#
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

#
# Set the default policy for the NAT table
#
iptables -t nat -P PREROUTING ACCEPT
iptables -t nat -P POSTROUTING ACCEPT
iptables -t nat -P OUTPUT ACCEPT

#
# Delete all rules
#
iptables -F
iptables -t nat -F

#
# Delete all chains
#

iptables -X
iptables -t nat -X

}


# To start the firewall
start() {
  echo -n "Iptables rules creation: "
  for f in /etc/firewall/*; do
  	source \$f
  done
  RETVAL=0
}

# To stop the firewall
stop() {
  echo -n "Removing all iptables rules: "
  disable_firewall
  RETVAL=0
}

case \$1 in
  start)
    start
    ;;
  stop)
    stop
    ;;
  restart)
    stop
    start
    ;;
  status)
    /sbin/iptables -L
    /sbin/iptables -t nat -L
    RETVAL=0
    ;;
  *)
    echo "Usage: firewall {start|stop|restart|status}"
    RETVAL=1
esac

exit

EOF_FIREWALL_INIT_D_SCRIPT
chmod 744 /etc/init.d/firewall
chown root.root /etc/init.d/firewall
echo "Created firewall init script"
fi

if [ $FIREWALL_ENABLE -ne 0 ]; then
	echo "Enable firewall"
	update-rc.d firewall defaults
fi


<?php
	}

};

?>

