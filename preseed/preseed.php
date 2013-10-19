<?php

# Netboot Images are located at:
# http://archive.ubuntu.com/ubuntu/dists/feisty/main/installer-i386/current/images/netboot/

require_once('preseed.config.inc');
require_once('Net/LDAP.php');
require_once('plugin.inc');


if(isset($_GET['info']))
{
	header('Content-Type: text/html');
	phpinfo();
	
	exit(0);
}

header('Content-Type: text/plain');

$param['base'] = $config['ldap']['base'];
$param['dn'] = $config['ldap']['binddn'];
$param['password'] = $config['ldap']['bindpasswd'];
$param['tls'] = $config['ldap']['tls'];
$param['host'] = $config['ldap']['server'];

$ldap = Net_Ldap::connect($param);
if (Net_Ldap::isError($ldap)) 
{ 
        print "# LDAP Error " . $ldap->getMessage() . "\n";
	exit;
}

function gethwaddrbyaddr($ip)
{
	$p = popen("/usr/sbin/arp -a -n $ip | grep -o -E '([a-fA-F0-9]{2}[:-]*){6}'",'r');
	while(!feof($p))
	{
		set_time_limit (20);
		$hwaddr = fgets($p, 4096);
	}
	pclose($p);
	return $hwaddr;
}

$client = array('ip' => $_SERVER['REMOTE_ADDR'],
	'name' => gethostbyaddr($_SERVER['REMOTE_ADDR']),
	'node' => '',
		'hwaddr' => gethwaddrbyaddr($_SERVER['REMOTE_ADDR']),
		'dhcp_hostname' => '',
		'class' => array('default'),
		'arch' => null,
		'distro' => '');

$dhcp_name = explode('.',$client['name']);
if(is_array($dhcp_name))
	$client['dhcp_hostname'] = $dhcp_name[0];
else
	$client['dhcp_hostname'] = $client['name'];

if(isset($_GET['client']))
	$client['name'] = $_GET['client'];
if(isset($_GET['class']))
	array_push($client['class'],$_GET['class']);
if(isset($_GET['node'])) {
	array_push($client['class'],$_GET['node']);
	$client['node'] = $_GET['node'];
}
if(isset($_GET['arch']))
	$client['arch'] = $_GET['arch'];
if(isset($_GET['distro']))
	$client['distro'] = $_GET['distro'];

if(isset($_GET['plugin']))
	$select_plugin = $_GET['plugin'];
else
	$select_plugin = '';

if(isset($_GET['script']))
{
	echo "#!/bin/bash\n";
	$output_script=$_GET['script'];
}
else
	$output_script='';

$search = @$ldap->search($config['ldap']['base'],
			"(&(objectClass=preseedObject)(preseedValue={$client['name']}))",
			array('scope' => 'sub'));

if (Net_Ldap::isError($search)) 
{
	print "# LDAP Error ". $entry->getMessage() . '\n';
} 
else 
{
	while(($entry = @$search->shiftEntry()) != false)
	{
		$class = @$entry->getValue('preseedValue');
		array_push($client['class'],$class);
	}
	$search->done();
}

$plugins = array();

// Find all plugins in configure directory

if ($handle = opendir($config['plugins']['directory'])) 
{
    while (false !== ($file = readdir($handle))) 
    {
        if ($file != "." && $file != "..") 
        {
		$fullname = $config['plugins']['directory'] . '/' . $file;
		$name = split('\\.',$file);
		if(strcmp($name[1],'inc') == 0)
		{
			$plugin_name = ucfirst($name[0]);
			if(empty($select_plugin) || strcasecmp($select_plugin,$plugin_name) == 0)
			{
				print "# Plugin $plugin_name";
				$classname = 'CPreseedPlugin' . $plugin_name;
				include_once($fullname);
				if (class_exists($classname)) {
					$plugin = new $classname($ldap,$client);
					$plugins[$plugin_name] = $plugin;
				}
			}
		}
        }
    }
    closedir($handle);
}

print "#\n";
print "# Preseed installer for machine {$client['name']} ({$client['ip']}, {$client['hwaddr']}, {$client['distro']})\n";
print "#\n\n";


print "#\n";
print "# Initialize Plugins\n";
print "#\n\n";
foreach($plugins as $plugin)
{
	$plugin->Initialize();
}

function get_script_cmdline($output_script)
{
	$url = get_script_url($output_script);

	$script_cmdline = "if [ -f /var/lib/preseed/log -a -d /target ]; then echo \"Preseed environment detected\"; DEST=/target/tmp/preseed_$output_script.sh; ";
	$script_cmdline = $script_cmdline . "SH=\"chroot /target /bin/sh\"; else echo \"Non-Preseed environment detected\"; DEST=/tmp/preseed_$output_script.sh; ";
	$script_cmdline = $script_cmdline . "SH=\"/bin/sh\"; fi; arch=`uname -m`; wget -q -O \$DEST \"{$url}\"; \$SH /tmp/preseed_$output_script.sh";
	return $script_cmdline;
}

function get_script_url($output_script)
{
	global $select_plugin;
	global $client;

	$script_url = 'http://' . $_SERVER['SERVER_NAME'] .  $_SERVER['SCRIPT_NAME'] . '?v=0';

	if(!empty($output_script)) 
		$script_url = $script_url . "&script=" . $output_script;
	
	if(isset($client['arch']))
		$script_url = $script_url . "&arch=" . $client['arch'];
	if(isset($client['distro']))
		$script_url = $script_url . "&distro=" . $client['distro'];
	
	if(!empty($select_plugin))
		$script_url = $script_url . "&plugin=$select_plugin";
#	if(isset($client['class']))
#		$script_url = $script_url . "&class={$client['class']}";
	if(isset($client['node']))
		$script_url = $script_url . "&node={$client['node']}";

	return $script_url;
}

if(empty($output_script))
{

	print 'd-i preseed/early_command string ' . get_script_cmdline('early') . "\n";

	# This command is run just before the install finishes, but when there is
	# still a usable /target directory.
	print 'd-i preseed/late_command string ' . get_script_cmdline('late') . "\n";

	print "#\n";
	print "# Perform preseed\n";
	print "#\n\n";
	foreach($plugins as $plugin)
	{
		$plugin->Preseed();
	}
}
else 
{
	# sample uname line
	# Linux ossrv 2.6.16.21-0.25-default #1 Tue Sep 19 07:26:15 UTC 2006 i686 athlon i386 GNU/Linux


	$script_cmdline = get_script_cmdline($output_script);

	$script_function_download = 
		"download_file() {\n" .
		"URL=\"$1\"\n" .
		"DEST=\"$2\"\n" .
		"if [ ! -z \"\$URL\" -a ! -z \"\$DEST\" ]; then\n" .
		"    wget -q -O \$DEST \"\$URL\" 2>&1\n" .
		"    RES=\$?\n" .
		"else\n" .
		"    RES=1\n" .
		"fi\n" .
		"return \$RES\n" .
		"}\n";

	if($output_script == 'early')
	{
		print "#\n";
		print "# Generate early script\n";
		print "# manual execute:\n";
		print "# $script_cmdline\n";

		print "# helper functions\n";
		print $script_function_download;
	
		print "#\n\n";
		print "echo \"Running early script\"\n";
		print "#\n\n";
		foreach($plugins as $plugin)
		{
			$plugin->ScriptEarly();
		}
		print "#\n\n";
		print "echo \"Finished early script\"\n";
		print "#\n\n";
	}
	else if($output_script == 'late')
	{
		print "#\n";
		print "# Generate late script\n";
		print "# manual execute:\n";
		print "# $script_cmdline\n";

		print "# helper functions\n";
		print $script_function_download;

		print "#\n\n";
		print "echo \"Running late script\"\n";
		print "#\n\n";

		foreach($plugins as $plugin)
		{
			$plugin->ScriptLate();
		}
		print "#\n\n";
		print "echo \"Finished late script\"\n";
		print "#\n\n";
	}
}

print "#\n";
print "# Deinitialize Plugins\n";
print "#\n\n";
foreach($plugins as $plugin)
{
	$plugin->Deinitialize();
}
$ldap->done();

print "#\n";
print "# EOF\n";
print "#\n";

?>
