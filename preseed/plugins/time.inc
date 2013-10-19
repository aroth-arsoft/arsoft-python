<?php

class CPreseedPluginTime extends CPreseedPluginBase
{
	private $m_params = array(
		'clock_utc' => array('preseed' => 'd-i clock-setup/utc boolean',
				'value' => 'true',
				'type' => 'boolean'),
		'timezone' => array('preseed' => 'd-i time/zone string',
				'value' => 'Europe/Berlin',
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
		print "# Date and Time parameters\n";
		print "#\n";

		$this->DefaultPreseed('time',$this->m_params);

	}	
};

?>

