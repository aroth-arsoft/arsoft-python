<?php

class CPreseedPluginCa extends CPreseedPluginBase
{
	private $m_params = array();

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
		global $config;
		print "#\n";
		print "# CA setup\n";
		print "#\n";

		return;
?>

# register certificates
#for f in /etc/arsoft/certs/*.crt; do ln -sf "$f" /etc/ssl/certs/`basename "$f"`; done 
#for f in /etc/arsoft/private/*.key; do ln -sf "$f" /etc/ssl/private/`basename "$f"`; done 

<?php
	}
};

?>

