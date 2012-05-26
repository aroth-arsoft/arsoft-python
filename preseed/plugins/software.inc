<?php

class CPreseedPluginSoftware extends CPreseedPluginBase
{
	private $m_params = array(
		'basic' => array('preseed' => 'tasksel tasksel/first multiselect',
				'value' => array('OpenSSH server'),
				'type' => 'multiselect'),
		'desktop' => array('preseed' => 'tasksel tasksel/desktop multiselect',
				'value' => array('kde'),
				'type' => 'multiselect'),
		'packages' => array('preseed' => 'd-i pkgsel/include string',
				'value' => '',
				'type' => 'string-array')
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
		print "# Software parameters\n";
		print "#\n";

		$this->DefaultPreseed('software',$this->m_params);
	}	
    public function ScriptLate()
    {
	    global $config;
	    print "#\n";
	    print "# Software setup\n";
	    print "#\n";
		
		print "echo \"update package index\"\n";
		print "apt-get update -q -y\n";
	
		print "echo \"install puppet on the installed system\"\n";
		print "wget -q -O - http://install.arsoft.homeip.net/puppetinstall | bash -\n";
	    $late_packages = $this->ReadString('software','late_packages', array(), 'array');

        if(is_array($late_packages))
        {
            foreach($late_packages as $pkg)
			{
				print "# install $pkg\n"
?>
x=`dpkg -s <?php echo $pkg; ?> 2>&1 >/dev/null`
RES=$?
if [ $RES -ne 0 ]; then
apt-get install -qq -y <?php echo $pkg . "\n"; ?> 
RES=$?
if [ $RES -eq 0 ]; then
	echo "Installed <?php echo $pkg; ?>"
else
	echo "Failed to install <?php echo $pkg; ?>"
fi
fi

<?php
			}
		}
	}	
};

?>

