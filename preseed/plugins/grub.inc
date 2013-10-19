<?php

class CPreseedPluginGrub extends CPreseedPluginBase
{
	private $m_params = array(
		'use_with_debian' => array('preseed' => 'grub-installer grub-installer/only_debian boolean',
				'value' => 'true',
				'type' => 'boolean'),
		'use_with_other_os' => array('preseed' => 'grub-installer grub-installer/with_other_os boolean',
				'value' => 'true',
				'type' => 'boolean'),
		'bootdev' => array('preseed' => 'grub-installer grub-installer/bootdev string',
				'value' => '(hd0)',
				'type' => 'string')
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
		print "# GRUB parameters\n";
		print "#\n";

		$this->DefaultPreseed('grub',$this->m_params);
	}
	public function ScriptLate()
	{
        print "#\n";
        print "# GRUB setup\n";
		print "#\n";

		return;
	
		$timeout = $this->ReadString('grub','timeout','6','integer'); 
		$hiddenmenu = $this->ReadString('grub','hiddenmenu','false','boolean');
		$splash = $this->ReadString('grub','splash','false','boolean');
		$menucolor = $this->ReadString('grub','menucolor','cyan/blue white/blue','string');
?>
	cat /boot/grub/menu.lst | \
		sed -e 's/^#*hiddenmenu$/<?php if($hiddenmenu == 'false') echo "#hiddenmenu"; else echo "hiddenmenu"; ?>/' | \
		sed 's/^timeout.*/timeout <?php echo $timeout; ?>/' | \
		sed 's@^#*color.*@<?php if($menucolor) echo "color " . $menucolor; else echo "#color cyan/blue white/blue"; ?>@' | \
		sed -r 's/^(kernel.*)splash(.*)/\1 \2/' | \
		sed -r 's/^(kernel.*)(quiet|verbose)(.*)/\1 verbose \3/' \
		> /tmp/menu.lst
		cp /tmp/menu.lst /boot/grub/menu.lst
<?php
	}	
};

?>

