<?php

class CPreseedPluginVmware extends CPreseedPluginBase
{
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
		print "#\n";
		print "# VMWare Workstation installation\n";
		print "#\n";
		$download_url = '';
		$vmware_arch = '';
		$install = $this->ReadString('vmware','install','false','boolean');
		if($install == 'true')
			$install = true;
		else
			$install = false;
		if($this->m_client['arch'] == 'i686')
		{
			$vmware_arch = 'i386';
			$download_url = $this->ReadString('vmware','url_32_bit',$download_url,'string');
		}
		else if($this->m_client['arch'] == 'x86_64')
		{
			$vmware_arch = 'x86_64';
			$download_url = $this->ReadString('vmware','url_64_bit',$download_url,'string');
		}

		if(!empty($download_url) && $install)
		{
?>

download_file "<?php echo $download_url; ?>" /tmp/vmware.deb
RES=$?
if [ $RES -eq 0 ]; then
	echo "Downloaded VMware package for <?php echo $vmware_arch; ?>"
	dpkg -i /tmp/vmware.deb
	if [ $RES -eq 0 ]; then
		echo "VMware  for <?php echo $vmware_arch; ?> installed"
	else
		echo "Failed to install VMware for <?php echo $vmware_arch; ?>"
	fi
else
	echo "Failed to download VMware package <?php echo $download_url; ?>"
fi
#rm -rf /tmp/vmware.deb
<?php
		}
	}	
};

?>

