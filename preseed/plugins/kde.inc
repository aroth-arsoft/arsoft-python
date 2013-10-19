<?php

class CPreseedPluginKde extends CPreseedPluginBase
{
	private $m_params = array();

	public function __construct($ldap,$client)
	{
		parent::__construct($ldap,$client);
	}

	public function Initialize()
	{
		$this->m_params = array(
		);
	}

	public function Deinitialze()
	{
	}

	public function Preseed()
	{
		print "#\n";
		print "# KDE parameters\n";
		print "#\n";

		$this->DefaultPreseed('kde',$this->m_params);
	}	
	public function ScriptLate()
	{
		global $config;
		print "#\n";
		print "# KDE setup\n";
		print "#\n";
		
		return;

        $profiles = $this->ReadString('kde','konqueror_profiles',array(),'array');
?>

if [ -d /usr/share/kubuntu-default-settings/kde-profile/default/share/apps/konqueror ]; then
	rm -rf /usr/share/kubuntu-default-settings/kde-profile/default/share/apps/konqueror
    if [ -e /usr/share/apps/konqueror/konqueror-orig.rc ]; then
	   cp /usr/share/apps/konqueror/konqueror-orig.rc /usr/share/apps/konqueror/konqueror.rc
    fi
fi

if [ -d /usr/share/kubuntu-default-settings/kde-profile/default/share/mimelnk/application/ ]; then
	rm -rf /usr/share/kubuntu-default-settings/kde-profile/default/share/mimelnk/application/
fi
<?php

        if(is_array($profiles))
        {
            foreach($profiles as $profile)
            {
?>

name=`basename "<?php echo $profile; ?>"`
if [ ! -f "/usr/share/apps/konqueror/profiles/$name" ]; then
download_file "<?php echo $profile; ?>" "/usr/share/apps/konqueror/profiles/$name"
RES=$?
if [ $RES -eq 0 ]; then
    echo "Installed profile $name"
else
    echo "Failed to install konqueror profile <?php echo $profile; ?>"
fi
fi

<?php
			}
		}
	}
};

?>

