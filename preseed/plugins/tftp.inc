<?php

class CPreseedPluginTftp extends CPreseedPluginBase
{
	private $m_params = array();

	public function __construct($ldap,$client)
	{
		parent::__construct($ldap,$client);
	}

	public function Initialize()
	{
		global $config;

	}

	public function Deinitialze()
	{
	}

	public function Preseed()
	{
		print "#\n";
		print "# TFTP parameters\n";
		print "#\n";

		$this->DefaultPreseed('tftp',$this->m_params);
	}	
	public function ScriptLate()
	{
		global $config;
		print "#\n";
		print "# TFTP setup\n";
		print "#\n";
		
		return;

		$enable_tftp = $this->ReadString('tftp','enable','false','boolean');
		
		$tftp_rootdir = $this->ReadString('tftp','rootdir','/var/lib/tftpboot','string');
		$pxelinux_cfg_default_url = $this->ReadString('tftp','pxelinux_default','','string');

		if($enable_tftp)
			$run_daemon = 'yes';
		else
			$run_daemon = 'no';

		$update_installer_script = $tftp_rootdir . '/update-installer.sh';
		$pxelinux_cfg = $tftp_rootdir . '/pxelinux.cfg';
		$pxelinux_0 = $tftp_rootdir . '/pxelinux.0';
		$pxelinux_0_32 = $tftp_rootdir . '/ubuntu-installer/i386/pxelinux.0';
		$pxelinux_0_64 = $tftp_rootdir . '/ubuntu-installer/i386/pxelinux.0';
		$pxelinux_cfg_default = $pxelinux_cfg . '/default';

		if($enable_tftp)
		{
?>

grep 'preseed/plugins/tftp.inc' /etc/default/tftpd-hpa 2>&1 > /dev/null
if [ $? -ne 0 ]; then
cat >> /etc/default/tftpd-hpa <<EOF_TFTPD_HPA_CONF
# preseed/plugins/tftp.inc 
# AR Soft specific LDAP configuration
#Defaults for tftpd-hpa
RUN_DAEMON="<?php echo $run_daemon; ?>"
OPTIONS="-l -s <?php echo $tftp_rootdir; ?>"

EOF_TFTPD_HPA_CONF
echo "adjustments to tftpd-hpa complete"
fi

if [ -d <?php echo $tftp_rootdir; ?> ]; then
if [ ! -e <?php echo $update_installer_script; ?> ]; then
cat >> <?php echo $update_installer_script; ?> <<EOF_TFTP_UPDATE_INSTALLER_SCRIPT
#!/bin/sh
# preseed/plugins/tftp.inc 
DIST='feisty'
BASE_URL='http://ftp.ubuntulinux.org/ubuntu/dists/'
INSTALLER32='/main/installer-i386/current/images/netboot/netboot.tar.gz'
INSTALLER64='/main/installer-amd64/current/images/netboot/netboot.tar.gz'
TFTPBOOT_DIR='<?php echo $tftp_rootdir; ?>'
TEMP_DIR='/tmp'
INSTALLER_FILES='./ubuntu-installer'

# helper functions
download_file() {
URL="\$1"
DEST="\$2"
if [ ! -z "\$URL" -a ! -z "\$DEST" ]; then
    wget -q -O \$DEST "\$URL" 2>&1
    RES=\$?
else
    RES=1
fi
return \$RES
}

echo "Download 32-Bit installer..."
download_file "\${BASE_URL}\${DIST}\${INSTALLER32}" \${TEMP_DIR}/netboot32.tar.gz
if [ \$? -eq 0 ]; then
	tar xfz \${TEMP_DIR}/netboot32.tar.gz -C \$TFTPBOOT_DIR "\$INSTALLER_FILES"
	if [ \$? -eq 0 ]; then
		echo "32-Bit installer updated"
	else
		echo "Failed to update 32-Bit installer"
	fi
	rm \${TEMP_DIR}/netboot32.tar.gz
else
	echo "Failed to download 32-Bit installer"
fi

echo "Download 64-Bit installer..."
download_file "\${BASE_URL}\${DIST}\${INSTALLER64}" \${TEMP_DIR}/netboot64.tar.gz
if [ \$? -eq 0 ]; then
	tar xfz \${TEMP_DIR}/netboot64.tar.gz -C \$TFTPBOOT_DIR "\$INSTALLER_FILES"
	if [ \$? -eq 0 ]; then
		echo "64-Bit installer updated"
	else
		echo "Failed to update 64-Bit installer"
	fi
	rm \${TEMP_DIR}/netboot64.tar.gz
else
	echo "Failed to download 64-Bit installer"
fi
EOF_TFTP_UPDATE_INSTALLER_SCRIPT
echo "update-installer script installed"
chmod +x '<?php echo $update_installer_script; ?>'

# Run update-installer script to retrieve the latest installers
<?php echo $update_installer_script; ?>

fi


if [ ! -d <?php echo $pxelinux_cfg; ?> ]; then
	mkdir '<?php echo $pxelinux_cfg; ?>'
fi

if [ ! -f '<?php echo $pxelinux_cfg_default; ?>' ]; then
download_file "<?php echo $pxelinux_cfg_default_url; ?>" <?php echo $pxelinux_cfg_default; ?> 2>&1
RES=$?
if [ $RES -eq 0 ]; then
	echo "pxelinux default config applied"
else
	echo "Failed to download pxelinux default config <?php echo $pxelinux_cfg_default_url; ?>"
fi
fi

if [ ! -h '<?php echo $pxelinux_0; ?>' ]; then
	ln -s '<?php echo $pxelinux_0_32; ?>' '<?php echo $pxelinux_0; ?>'
fi

fi

<?php
		} // if($enable_tftp)

	}

};

?>

