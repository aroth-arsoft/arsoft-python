<?php

class CPreseedPluginJava extends CPreseedPluginBase
{
	private $m_params = array(
		'accept-dlj-v1' => array('preseed' => array('sun-java5-bin shared/accepted-sun-dlj-v1-1 boolean',
												'sun-java5-jre shared/accepted-sun-dlj-v1-1 boolean'),
				'value' => 'true',
				'type' => 'boolean'),
		'jcepolicy' => array('preseed' => 'sun-java5-jre sun-java5-jre/jcepolicy note',
				'value' => null,
				'type' => 'string'),
		'stopthread' => array('preseed' => 'sun-java5-jre sun-java5-jre/stopthread boolean',
				'value' => 'true',
				'type' => 'boolean'),
		'error-dlj-v1' => array('preseed' => array('sun-java5-bin shared/error-sun-dlj-v1-1 error',
												'sun-java5-jre shared/error-sun-dlj-v1-1 error'),
				'value' => null,
				'type' => 'string'),
		'present-dlj-v1' => array('preseed' => array('sun-java5-bin shared/present-sun-dlj-v1-1 note',
												'sun-java5-jre shared/present-sun-dlj-v1-1 note'),
				'value' => null,
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
		print "# Java parameters\n";
		print "#\n";

		$this->DefaultPreseed('java',$this->m_params);
	}	
};

?>

