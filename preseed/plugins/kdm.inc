<?php

class CPreseedPluginKdm extends CPreseedPluginBase
{
	private $m_params = array();

	public function __construct($ldap,$client)
	{
		parent::__construct($ldap,$client);
	}

	public function Initialize()
	{
		$this->m_params = array(
		'stop_with_children' => array('preseed' => 'kdm kdm/stop_running_server_with_children boolean false',
				'value' => 'false',
				'type' => 'boolean'),
		'display_manager' => array('preseed' => array('kdm shared/default-x-display-manager select',
                                                        'kdm-kde4 shared/default-x-display-manager select'),
				'value' => 'kdm',
				'type' => 'string'),
		'daemon' => array('preseed' => 'kdm kdm/daemon_name string',
				'value' => '/usr/bin/kdm',
				'type' => 'string')
		);
	}

	public function Deinitialze()
	{
	}

	public function Preseed()
	{
		print "#\n";
		print "# KDM parameters\n";
		print "#\n";

		$this->DefaultPreseed('kdm',$this->m_params);
	}	
	public function ScriptLate()
	{
		global $config;
		print "#\n";
		print "# KDM setup\n";
		print "#\n";

		return;
		
		$theme_file = $this->ReadString('kdm','theme','','string');
		$wallpaper_file = $this->ReadString('kdm','wallpaper','','string');

		$root_login = $this->ReadString('kdm','root_login','true','boolean');

		$auto_login = $this->ReadString('kdm','auto_login','false','boolean');
		$auto_relogin = $this->ReadString('kdm','auto_relogin','true','boolean');
		$auto_login_user = $this->ReadString('kdm','auto_login_user','','string');
		$auto_login_pass = $this->ReadString('kdm','auto_login_pass','','string');
		$no_pass_users = $this->ReadString('kdm','no_pass_users','','string');

?>
THEME_URL=<?php echo $theme_file; print "\n"; ?>
WALLPAPER_URL=<?php echo $wallpaper_file; print "\n";  ?>

THEME_FILE=`echo -n "/tmp/"; basename "$THEME_URL"`
WALLPAPER_FILE=`echo -n "/tmp/"; basename "$THEME_URL"`
KDMRC=/etc/kde3/kdm/kdmrc
BACKGROUNDRC=/etc/kde3/kdm/backgroundrc
KDM_THEME_DIR=/usr/share/apps/kdm/themes/
WALLPAPER_DEST_FILE=`echo -n "/usr/share/wallpapers/"; basename "$WALLPAPER_URL"`

is_bz2=`echo "$THEME_FILE" | grep bz2`
is_gz=`echo "$THEME_FILE" | grep gz`

if [ ! -z "$is_bz2" ]; then
	tar_opt='jf'
fi
if [ ! -z "$is_gz" ]; then
	tar_opt='zf'
fi

download_file "$WALLPAPER_URL" $WALLPAPER_FILE 2>&1
RES=$?
if [ $RES -eq 0 ]; then
	cat "$BACKGROUNDRC" | sed "s@^Wallpaper=.*@Wallpaper=$WALLPAPER_DEST_FILE@" > /tmp/backgroundrc && cp /tmp/backgroundrc $BACKGROUNDRC
	echo "KDM wallpaper patched"
else
	echo "Failed to download KDM wallpaper $WALLPAPER_URL"
fi

download_file "$THEME_URL" $THEME_FILE
RES=$?
if [ $RES -eq 0 ]; then
	if [ ! -z "$tar_opt" ]; then
		tar_dir=`tar t$tar_opt $THEME_FILE 2>&1 | head -n 1`
		RES=$?
		if [ $RES -eq 0 ]; then
			new_theme_dir="$KDM_THEME_DIR/$tar_dir"
			tar x$tar_opt $THEME_FILE -C $KDM_THEME_DIR 2>&1 > /dev/null
			RES=$?
			if [ $RES -eq 0 ]; then	
				cat "$KDMRC" | sed 's@^#*UseTheme=.*@UseTheme=true@' | sed "s@^#*Theme=.*@Theme=$new_theme_dir@" > /tmp/kdmrc && cp /tmp/kdmrc $KDMRC
				echo "KDM configuration patched"
			fi
		fi
	fi
else
	echo "Failed to download KDM theme $THEME_URL"
fi

cat "$KDMRC" | sed 's@^#*AllowRootLogin=.*@AllowRootLogin=<?php echo $root_login; ?>@' > /tmp/kdmrc && cp /tmp/kdmrc $KDMRC && echo "KDM root login configured (<?php echo $root_login; ?>)"

cat "$KDMRC" | sed 's@^#*AutoReLogin=.*@AutoReLogin=<?php echo $auto_relogin; ?>@' > /tmp/kdmrc && cp /tmp/kdmrc $KDMRC && echo "KDM auto re-login configured (<?php echo $auto_relogin; ?>)"

cat "$KDMRC" | sed 's@^#*AutoLoginEnable=.*@AutoLoginEnable=<?php echo $auto_login; ?>@' > /tmp/kdmrc && cp /tmp/kdmrc $KDMRC && echo "KDM auto login configured (<?php echo $auto_login; ?>)"

cat "$KDMRC" | sed 's@^#*AutoLoginUser=.*@AutoLoginUser=<?php echo $auto_login_user; ?>@' > /tmp/kdmrc && cp /tmp/kdmrc $KDMRC && echo "KDM auto login user configured (<?php echo $auto_login_user; ?>)"

cat "$KDMRC" | sed 's@^#*AutoLoginPass=.*@AutoLoginPass=<?php echo $auto_login_pass; ?>@' > /tmp/kdmrc && cp /tmp/kdmrc $KDMRC && echo "KDM auto login pass configured (<?php echo $auto_login_pass; ?>)"

cat "$KDMRC" | sed 's@^#*NoPassUsers=.*@NoPassUsers=<?php echo $no_pass_users; ?>@' > /tmp/kdmrc && cp /tmp/kdmrc $KDMRC && echo "KDM no password users configured (<?php echo $no_pass_users; ?>)"

<?php
	}
};

?>

