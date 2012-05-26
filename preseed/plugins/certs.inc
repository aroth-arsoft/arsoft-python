<?php

class CPreseedPluginCerts extends CPreseedPluginBase
{
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
		print "#\n";
		print "# AR Soft Certificate installation\n";
		print "#\n";
		
		return;

		$base_url = $this->ReadString('certs','base_url','','string');
		$certificates = $this->ReadString('certs','certificates',array(),'array');

#	print "echo $base_url\n";
#print "echo $certificates\n";
?>
if [ ! -d /etc/arsoft/certs ]; then
	mkdir -p /etc/arsoft/certs
fi


<?php

		if(is_array($certificates))
		{
			foreach($certificates as $cert)
			{
?>


download_file "<?php echo $base_url . '/' . $cert; ?>" '/etc/arsoft/certs/<?php echo $cert; ?>'
RES=$?
if [ $RES -eq 0 ]; then
	echo "Downloaded certificate <?php echo $cert; ?>"
	name=`basename <?php echo $cert; ?> .crt`
	[ ! -d /etc/ssl/certs ] && mkdir -p /etc/ssl/certs
	ln -sf '/etc/arsoft/certs/<?php echo $cert; ?>' "/etc/ssl/certs/$name.pem"
	<?php if ($cert == 'root.crt') { ?>
		cat '/etc/arsoft/certs/<?php echo $cert; ?>' >> /etc/ssl/certs/ca-certificates.crt
    <?php } ?>		
else
	echo "Failed to download certificate <?php echo $cert; ?>"
fi

<?php
			}
		}
	}	
};

?>

