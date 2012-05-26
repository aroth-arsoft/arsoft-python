<?php

class CPreseedPluginNfs extends CPreseedPluginBase
{
	private $m_params = array(
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
		print "# NFS parameters\n";
		print "#\n";

		$this->DefaultPreseed('nfs',$this->m_params);
	}	
    public function ScriptLate()
    {
	    global $config;
	    print "#\n";
	    print "# NFS setup\n";
	    print "#\n";
	
		return;
		
		$need_lockd = $this->ReadString('nfs','lockd', 'false', 'boolean');
		$need_gssd = $this->ReadString('nfs','gssd','true','boolean');
		$need_idmapd = $this->ReadString('nfs','idmapd','true','boolean');
		$statd_opts = $this->ReadString('nfs','statd_options','','string');

		
	
?>

grep 'preseed/plugins/nfs.inc' /etc/default/nfs-common 2>&1 > /dev/null
if [ $? -ne 0 ]; then
cat > /etc/default/nfs-common <<EOF_NFS_COMMON
# preseed/plugins/nfs.inc
# If you do not set values for the NEED_ options, they will be attempted
# autodetected; this should be sufficient for most people. Valid alternatives
# for the NEED_ options are "yes" and "no".

# Options for rpc.statd.
#   Should rpc.statd listen on a specific port? This is especially useful
#   when you have a port-based firewall. To use a fixed port, set this
#   this variable to a statd argument like: "--port 4000 --outgoing-port 4001".
#   For more information, see rpc.statd(8) or http://wiki.debian.org/?SecuringNFS
STATDOPTS=<?php echo $statd_opts . "\n"; ?>

# Some kernels need a separate lockd daemon; most don't. Set this if you
# want to force an explicit choice for some reason.
NEED_LOCKD=<?php if($need_lockd == 'true') echo "yes\n"; else echo "no\n"; ?>

# Do you want to start the idmapd daemon? It is only needed for NFSv4.
NEED_IDMAPD=<?php if($need_idmapd == 'true') echo "yes\n"; else echo "no\n"; ?>

# Do you want to start the gssd daemon? It is required for Kerberos mounts.
NEED_GSSD=<?php if($need_gssd == 'true') echo "yes\n"; else echo "no\n"; ?>

EOF_NFS_COMMON
echo "adjustments to /etc/default/nfs-common complete"
fi

<?php
	}
};

?>

