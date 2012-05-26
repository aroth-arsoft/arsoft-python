<?php

class CPreseedPluginSetup extends CPreseedPluginBase
{
	private $m_params = array(
		'keymap' => array('preseed' => 'd-i debian-installer/keymap string',
				'value' => 'us',
				'type' => 'string'),
		'keyboard' => array('preseed' => array('d-i kbd-chooser/method select',
												'console-setup console-setup/layoutcode string'),
				'value' => 'us',
				'type' => 'string'),
        'layout' => array('preseed' => 'console-setup console-setup/layout select',
		                'value' => 'USA',
						'type' => 'string'),
        'detect_layout' => array('preseed' => 'console-setup console-setup/ask_detect boolean',
                        'value' => 'false',
				        'type' => 'boolean'),
		'locale' => array('preseed' => 'd-i debian-installer/locale string',
				'value' => 'en_US',
				'type' => 'string'),
		'no_intro_msg' => array('preseed' => 'base-config base-config/intro note',
				'value' => '',
				'type' => 'note'),
		'no_login_msg' => array('preseed' => 'base-config base-config/login note',
				'value' => '',
				'type' => 'note'),
		'no_reboot_msg' => array('preseed' => 'd-i prebaseconfig/reboot_in_progress note',
				'value' => '',
				'type' => 'note'),
		'no_finish_msg' => array('preseed' => 'd-i finish-install/reboot_in_progress note',
				'value' => '',
				'type' => 'note'),
		'popularity-contest' => array('preseed' => 'popularity-contest popularity-contest/participate boolean',
				'value' => 'false',
				'type' => 'boolean'),
		'encrypted_homedir' => array('preseed' => 'user-setup-udeb user-setup/encrypted-private boolean',
				'value' => 'false',
				'type' => 'boolean'),

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
		print "# Setup parameters\n";
		print "#\n";

		$this->DefaultPreseed('setup',$this->m_params);
	}	
};

?>

