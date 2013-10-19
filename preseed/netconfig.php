<?php

# Netboot Images are located at:
# http://archive.ubuntu.com/ubuntu/dists/feisty/main/installer-i386/current/images/netboot/

require_once('preseed.config.inc');
require_once('Net/LDAP.php');
require_once('plugin.inc');


header('Content-Type: text/html');

$param['base'] = 'o=arsoft';
$param['dn'] = 'cn=Manager,o=arsoft';
$param['password'] = 'jupiter';
$param['tls'] = false;
$param['host'] = 'ar.arsoft.homeip.net';

echo "<HTML><HEAD><TITLE>AR Soft Network config</TITLE></HEAD>";
echo "<BODY>";
$ldap = Net_Ldap::connect($param);
if (Net_Ldap::isError($ldap))
{
        print "# LDAP Error " . $ldap->getMessage() . "\n";
    exit;
}
/*



$nodes = array();
$classes = array();

$search = @$ldap->search($param['base'],
            "(objectClass=netconfigNode)",
            array('scope' => 'sub'));

if (Net_Ldap::isError($search))
{
    print "# LDAP Error ". $entry->getMessage() . '\n';
}
else
{
    while(($entry = @$search->shiftEntry()) != false)
    {
	$node = array();
        $node['name'] = @$entry->getValue('cn');
        array_push($nodes,$node);
    }
    $search->done();
}

$search = @$ldap->search($param['base'],
            "(objectClass=netconfigClass)",
            array('scope' => 'sub'));

if (Net_Ldap::isError($search))
{
    print "# LDAP Error ". $entry->getMessage() . '\n';
}
else
{
    while(($entry = @$search->shiftEntry()) != false)
    {
	$class = array();
        $class['name'] = @$entry->getValue('cn');
        array_push($classes,$class);
    }
    $search->done();
}
echo "<TABLE width='100%' cellspacing='0' border='0'>";
echo "<TH><TD>Name</TD></TH>";
foreach($nodes as $node)
{
	echo "<TR><TD>{$node['name']}</TD></TR>";
}
echo "</TABLE>";

echo "<TABLE width='100%' cellspacing='0' border='0'>";
echo "<TH><TD>Name</TD></TH>";
foreach($classes as $class)
{
	echo "<TR><TD>{$class['name']}</TD></TR>";
}
echo "</TABLE>";
*/

echo "</BODY></HTML>";

?>

