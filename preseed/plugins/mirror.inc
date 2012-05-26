<?php

class CPreseedPluginMirror extends CPreseedPluginBase
{
	private $m_params = array();

	public function __construct($ldap,$client)
	{
		parent::__construct($ldap,$client);
	}

	public function Initialize()
	{
		global $config;
		$this->m_params = array(
		'uri_type' => array('preseed' => 'base-config apt-setup/uri_type select',
				'value' => $config['apt']['uri_type'],
				'type' => 'string'),
		'country' => array('preseed' => 'base-config apt-setup/country select',
				'value' => 'enter information manually',
				'type' => 'string'),
		'country' => array('preseed' => 'd-i  mirror/country string',
				'value' => 'enter information manually',
				'type' => 'string'),
		'hostname' => array('preseed' => 'base-config apt-setup/hostname string',
				'value' => $config['apt']['server'] . ':' . $config['apt']['port'],
				'type' => 'string'),
		'directory' => array('preseed' => 'base-config apt-setup/directory string',
				'value' => $config['apt']['directory'],
				'type' => 'string'),
		'use_nonfree' => array('preseed' => 'base-config apt-setup/non-free boolean',
				'value' => 'true',
				'type' => 'boolean'),
		'use_another' => array('preseed' => 'base-config apt-setup/another boolean',
				'value' => 'false',
				'type' => 'boolean'),
		'use_contrib' => array('preseed' => 'base-config apt-setup/contrib boolean',
				'value' => 'true',
				'type' => 'boolean'),
		'use_security_updates' => array('preseed' => 'base-config apt-setup/security-updates boolean',
				'value' => 'true',
				'type' => 'boolean'),
		'use_universe' => array('preseed' => 'base-config apt-setup/universe boolean',
				'value' => 'true',
				'type' => 'boolean'),
		'use_backports' => array('preseed' => 'base-config apt-setup/backports boolean',
				'value' => 'true',
				'type' => 'boolean'),
		'suite' => array('preseed' => 'd-i mirror/suite string',
				#'value' => $config['apt']['suite'],
				'value' => $this->m_client['distro'],
				'type' => 'string'),
		'http_proxy' => array('preseed' => 'd-i mirror/http/proxy string',
				'value' => $config['apt']['proxy'],
				'type' => 'string'),
		'http_country' => array('preseed' => 'd-i mirror/country select',
				'value' => $config['apt']['mirror_country'],
				'type' => 'string'),
		'http_hostname' => array('preseed' => 'd-i mirror/http/hostname string',
				'value' => $config['apt']['server'] . ':' . $config['apt']['port'],
				'type' => 'string'),
		'http_mirror' => array('preseed' => 'd-i mirror/http/mirror string',
				'value' => $config['apt']['server'] . ':' . $config['apt']['port'],
				'type' => 'string'),
		'http_directory' => array('preseed' => 'd-i mirror/http/directory string',
				'value' => $config['apt']['directory'],
				'type' => 'string'),
		'http_countries' => array('preseed' => 'd-i  mirror/http/countries select',
				'value' => 'enter information manually',
				'type' => 'string'),
		'ftp_countries' => array('preseed' => 'd-i  mirror/ftp/countries select',
				'value' => 'enter information manually',
				'type' => 'string'),
		'update-policy' => array('preseed' => 'd-i pkgsel/update-policy select',
				'value' => 'none',
				'type' => 'string'),
				
		);

	}

	public function Deinitialze()
	{
	}

	public function Preseed()
	{
		print "#\n";
		print "# Mirror parameters\n";
		print "#\n";

		while(list($name, $val) = each($this->m_params))
		{
			
			$val['value'] = $this->ReadString('mirror',$name, $val['value'], $val['type']);

			print "{$val['preseed']} {$val['value']}\n";
		}
	}	
	public function ScriptLate()
	{
		global $config;
		print "#\n";
		print "# Mirror setup\n";
		print "#\n";

		return;
		
		$val = $this->m_params['hostname'];
		$val['value'] = $this->ReadString('mirror','hostname', $val['value'], $val['type']);

?>

cat /etc/apt/sources.list | sed s@security.ubuntu.com@<?php echo $val['value']; ?>@ > /tmp/sources.list
cp /tmp/sources.list /etc/apt/sources.list
DISTRIB_CODENAME=`grep DISTRIB_CODENAME /etc/lsb-release | cut -f 2 -d '='`

APT_GET_UPDATE=0
#if [ ! -f /etc/apt/sources.list.d/wine.list ]; then
#echo "## WineHQ - $DISTRIB_CODENAME" >> /etc/apt/sources.list.d/wine.list
#echo "deb http://<?php echo $val['value']; ?>/wine $DISTRIB_CODENAME main" >> /etc/apt/sources.list.d/wine.list
#echo "deb-src http://<?php echo $val['value']; ?>/wine $DISTRIB_CODENAME main" >> /etc/apt/sources.list.d/wine.list

## Import key for Wine
#wget -q http://wine.budgetdedicated.com/apt/387EE263.gpg -O- | apt-key add -
#APT_GET_UPDATE=1
#fi

if [ ! -f /etc/apt/sources.list.d/kde3.list ]; then
echo "## KDE Updates - $DISTRIB_CODENAME" >> /etc/apt/sources.list.d/kde3.list
echo "deb http://<?php echo $val['value']; ?>/kde3 $DISTRIB_CODENAME main" >> /etc/apt/sources.list.d/kde3.list
echo "deb-src http://<?php echo $val['value']; ?>/kde3 $DISTRIB_CODENAME main" >> /etc/apt/sources.list.d/kde3.list

# Import key for KDE
wget -q http://kubuntu.org/announcements/kubuntu-packages-jriddell-key.gpg -O- | apt-key add -
APT_GET_UPDATE=1
fi

if [ "$DISTRIB_CODENAME" = "gutsy" ]; then
if [ ! -f /etc/apt/sources.list.d/kde4.list ]; then
echo "## KDE Updates - $DISTRIB_CODENAME" >> /etc/apt/sources.list.d/kde4.list
echo "deb http://<?php echo $val['value']; ?>/kde4 $DISTRIB_CODENAME main" >> /etc/apt/sources.list.d/kde4.list
echo "deb-src http://<?php echo $val['value']; ?>/kde4 $DISTRIB_CODENAME main" >> /etc/apt/sources.list.d/kde4.list

# Import key for KDE
wget -q http://kubuntu.org/announcements/kubuntu-packages-jriddell-key.gpg -O- | apt-key add -
APT_GET_UPDATE=1
fi
fi

if [ ! -f /etc/apt/sources.list.d/arsoft.list ]; then
echo "## AR Soft packages - $DISTRIB_CODENAME" >> /etc/apt/sources.list.d/arsoft.list
echo "deb http://<?php echo $config['arsoft']['server']; ?>/arsoft $DISTRIB_CODENAME main" >> /etc/apt/sources.list.d/arsoft.list
echo "deb-src http://<?php echo $config['arsoft']['server']; ?>/arsoft $DISTRIB_CODENAME main" >> /etc/apt/sources.list.d/arsoft.list

# Import key for AR Soft
wget -q http://<?php echo $config['arsoft']['server']; ?>/arsoft/arsoft.asc -O- | apt-key add -
APT_GET_UPDATE=1
fi

if [ ! -f /etc/apt/sources.list.d/medibuntu.list ]; then
echo "## Medibuntu - Ubuntu $DISTRIB_CODENAME" >> /etc/apt/sources.list.d/medibuntu.list
echo "## Please report any bug on https://launchpad.net/products/medibuntu/+bugs" >> /etc/apt/sources.list.d/medibuntu.list
echo "deb http://<?php echo $val['value']; ?>/medibuntu $DISTRIB_CODENAME free non-free" >> /etc/apt/sources.list.d/medibuntu.list
echo "deb-src http://<?php echo $val['value']; ?>/medibuntu $DISTRIB_CODENAME free non-free" >> /etc/apt/sources.list.d/medibuntu.list

# Import key for Medibuntu
wget -q http://packages.medibuntu.org/medibuntu-key.gpg -O- | apt-key add -
APT_GET_UPDATE=1
fi

if [ $APT_GET_UPDATE -ne 0 ]; then
	echo "Update apt package list"
	apt-get update -y -qq
fi


<?php
	}
};

?>

