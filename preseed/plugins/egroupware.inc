<?php

class CPreseedPluginEgroupware extends CPreseedPluginBase
{
	private $m_params = array();

	public function __construct($ldap,$client)
	{
		parent::__construct($ldap,$client);
	}

	public function Initialize()
	{
		global $config;
/*



     
*/

		$this->m_params = array(
		'config_note' => array('preseed' => 'egroupware-core egroupware/configuration/note note',
				'value' => '',
				'type' => 'note'),
		'header_password' => array('preseed' => array(
					'egroupware-core egroupware/header/password password',
					'egroupware-core egroupware/header/password/confirm password'),
				'value' => 'secret',
				'type' => 'string'),
		'header_user' => array('preseed' => 'egroupware-core egroupware/header/user string',
				'value' => 'admin',
				'type' => 'string'),
		'webserver' => array('preseed' => 'egroupware-core egroupware/webserver multiselect',
				'value' => 'Apache 2',
				'type' => 'string')
		);
	}

	public function Deinitialze()
	{
	}

	public function Preseed()
	{
		print "#\n";
		print "# eGroupware parameters\n";
		print "#\n";

		$this->DefaultPreseed('egroupware',$this->m_params);
	}	
};

?>

