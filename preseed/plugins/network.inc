<?php

class CPreseedPluginNetwork extends CPreseedPluginBase
{
	private $m_params = array();

	public function __construct($ldap,$client)
	{
		parent::__construct($ldap,$client);
	}

	public function Initialize()
	{
		global $config;
		global $client;
		$this->m_params = array(
		'use_dhcp' => array('preseed' => 'netcfg netcfg/use_dhcp boolean',
				'value' => 'true',
				'type' => 'boolean'),
		'disable_dhcp' => array('preseed' => 'netcfg netcfg/disable_dhcp boolean',
				'value' => 'false',
				'type' => 'boolean'),
		'dhcp_failed' => array('preseed' => 'netcfg netcfg/dhcp_failed note',
				'value' => '',
				'type' => 'note'),
		'no_dhcp_error' => array('preseed' => 'netcfg netcfg/no_dhcp_client error',
				'value' => '',
				'type' => 'error'),
		# d-i netcfg/dhcp_options select Configure network manually
		'dhcp_options' => array('preseed' => 'netcfg netcfg/dhcp_options select',
				'value' => 'Retry network autoconfiguration',
				'type' => 'string'),
		'dhcp_hostname' => array('preseed' => 'netcfg netcfg/dhcp_hostname string',
				'value' => $client['dhcp_hostname'],
				'type' => 'string'),
		# Any hostname and domain names assigned from dhcp take precedence over
		# values set here. However, setting the values still prevents the questions
		# from being shown, even if values come from dhcp.
		'get_hostname' => array('preseed' => 'netcfg netcfg/get_hostname string',
				'value' => 'unassigned-hostname',
				'type' => 'string'),
		'get_domain' => array('preseed' => 'netcfg netcfg/get_domain string',
				'value' => 'unassigned-domain',
				'type' => 'string'),
		'get_nameservers' => array('preseed' => 'netcfg netcfg/get_nameservers string',
				'value' => '',
				'type' => 'string'),
		'get_ipaddress' => array('preseed' => 'netcfg netcfg/get_ipaddress string',
				'value' => '',
				'type' => 'string'),
		'get_netmask' => array('preseed' => 'netcfg netcfg/get_netmask string',
				'value' => '',
				'type' => 'string'),
		'get_gateway' => array('preseed' => 'netcfg netcfg/get_gateway string',
				'value' => '',
				'type' => 'string'),
		'confirm_static' => array('preseed' => 'netcfg netcfg/confirm_static boolean',
				'value' => 'true',
				'type' => 'boolean'),
		# Disable that annoying WEP key dialog.
		'wireless_wep' => array('preseed' => 'netcfg netcfg/wireless_wep string',
				'value' => '',
				'type' => 'string')
		);
	}

	public function Deinitialze()
	{
	}

	public function Preseed()
	{
		print "#\n";
		print "# Network parameters\n";
		print "#\n";

		$this->DefaultPreseed('network',$this->m_params);
	}	
	public function ScriptLate()
	{
		global $config;
		print "#\n";
		print "# LDAP setup\n";
		print "#\n";
		
		return;

?>
		[ -f /etc/dhcp3/dhclient.conf.dpkg-dist ] && mv /etc/dhcp3/dhclient.conf.dpkg-dist /etc/dhcp3/dhclient.conf
<?php
	}
};

?>

