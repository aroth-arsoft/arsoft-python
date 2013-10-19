<?php

$config['plugins'] = array(
	'directory' => './plugins'
);

$config['common'] = 'common';

$config['apt'] = array(
	'server' => 'mirror.switch.ch',
	'port' => '80',
	'uri_type' => 'http',
	'directory' => '/ftp/mirror/ubuntu/',
	'suite' => 'maverick',
	'mirror_country' => 'enter information manually',
	'proxy' => 'http://install.arsoft.homeip.net:3142'
);

$config['ldap'] = array(
	'server' => 'ldap.arsoft.homeip.net',
	'port' => 389,
	'tls' => false,
	'base' => 'ou=preseed,ou=config,dc=arsoft,dc=homeip,dc=net,o=arsoft',
	'binddn' => null,
	'bindpasswd' => null
);

$config['arsoft'] = array(
	'server' => 'install.arsoft.homeip.net'
);

?>
