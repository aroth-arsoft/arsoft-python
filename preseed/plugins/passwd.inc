<?php

class CPreseedPluginPasswd extends CPreseedPluginBase
{
	private $m_params = array(
		'make-user' => array('preseed' => 'd-i passwd/make-user boolean',
				'value' => 'false',
				'type' => 'boolean'),
		'fullname' => array('preseed' => 'passwd passwd/user-fullname string',
				'value' => null,
				'type' => 'string'),
		'username' => array('preseed' => 'passwd passwd/username string',
				'value' => null,
				'type' => 'string'),
		'password' => array('preseed' => 'passwd passwd/user-password string',
				'value' => null,
				'type' => 'string'),
		'password-confirm' => array('preseed' => 'passwd passwd/user-password-again string',
				'value' => null,
				'type' => 'string'),
		'root-login' => array('preseed' => 'd-i passwd/root-login boolean',
				'value' => 'true',
				'type' => 'boolean'),
		'root-password' => array('preseed' => array('d-i passwd/root-password password',
													'd-i passwd/root-password-again password'),
				'value' => 'mungobohne',
	            'type' => 'string'),
		'password-md5' => array('preseed' => 'passwd passwd/md5 boolean',
				'value' => 'false',
				'type' => 'boolean'),
		'password-shadow' => array('preseed' => 'passwd passwd/shadow boolean',
				'value' => 'true',
				'type' => 'boolean')
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
		print "# Passwd parameters\n";
		print "#\n";

		$this->DefaultPreseed('passwd',$this->m_params);
	}	
};

?>

