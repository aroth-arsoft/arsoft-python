<?php

class CPreseedPluginX11 extends CPreseedPluginBase
{
	private $m_params = array(
		'driver' => array('preseed' => 'xserver-xorg xserver-xorg/config/device/driver select',
				'value' => 'vesa',
				'type' => 'string'),
		'server' => array('preseed' => 'xserver-xorg shared/default-x-server select',
				'value' => 'xserver-org',
				'type' => 'string'),

		'write_files_section' => array('preseed' => 'xserver-xorg xserver-xorg/config/write_files_section boolean',
				'value' => 'true',
				'type' => 'boolean'),
		'mouse_autodetect' => array('preseed' => 'xserver-xorg xserver-xorg/config/autodetect_mouse boolean',
				'value' => 'true',
				'type' => 'boolean'),
		'mouse_port' => array('preseed' => 'xserver-xorg xserver-xorg/config/inputdevice/mouse/port select',
				'value' => '/dev/input/mice',
				'type' => 'string'),
		'mouse_emulate3buttons' => array('preseed' => 'xserver-xorg xserver-xorg/config/emulate3buttons boolean',
				'value' => 'false',
				'type' => 'boolean'),
		'mouse_protocol' => array('preseed' => 'xserver-xorg xserver-xorg/config/inputdevice/mouse/protocol select',
				'value' => '',
				'type' => 'string'),
		'keyboard_rules' => array('preseed' => 'xserver-xorg xserver-xorg/config/inputdevice/keyboard/rules string',
				'value' => 'xorg',
				'type' => 'string'),
		'keyboard_layout' => array('preseed' => 'xserver-xorg xserver-xorg/config/inputdevice/keyboard/layout string',
				'value' => 'us',
				'type' => 'string'),
		'keyboard_model' => array('preseed' => 'xserver-xorg xserver-xorg/config/inputdevice/keyboard/model string',
				'value' => 'pc105',
				'type' => 'string'),

		'monitor_id' => array('preseed' => 'xserver-xorg xserver-xorg/config/monitor/identifier string',
				'value' => 'Monitor0',
				'type' => 'string'),
		'monitor_selection' => array('preseed' => 'xserver-xorg xserver-xorg/config/monitor/selection-method select',
				'value' => 'medium',
				'type' => 'string'),
		'monitor_autodetect' => array('preseed' => 'xserver-xorg xserver-xorg/autodetect_monitor boolean',
				'value' => 'true',
				'type' => 'boolean'),
		'monitor_lcd' => array('preseed' => 'xserver-xorg xserver-xorg/config/monitor/lcd boolean',
				'value' => 'false',
				'type' => 'boolean'),
		'monitor_sync_ranges' => array('preseed' => 'xserver-xorg xserver-xorg/config/monitor/use_sync_ranges boolean',
				'value' => 'false',
				'type' => 'boolean'),
		'monitor_modeline' => array('preseed' => 'xserver-xorg xserver-xorg/config/monitor/mode-list select',
				'value' => '',
				'type' => 'string'),
		'monitor_size' => array('preseed' => 'xserver-xorg xserver-xorg/config/monitor/screen-size select',
				'value' => '19 inches',
				'type' => 'string'),
		'monitor_vsync' => array('preseed' => 'xserver-xorg xserver-xorg/config/monitor/vert-refresh string',
				'value' => '',
				'type' => 'string'),
		'monitor_hsync' => array('preseed' => 'xserver-xorg xserver-xorg/config/monitor/horiz-sync string',
				'value' => '',
				'type' => 'string'),

		'display_depth' => array('preseed' => 'xserver-xorg xserver-xorg/config/display/default_depth select',
				'value' => '24',
				'type' => 'integer'),
		'display_mode' => array('preseed' => 'd-i xserver-xorg/config/display/modes multiselect',
				'value' => '1280x1024',
				'type' => 'string'),

		'modules' => array('preseed' => 'xserver-xorg xserver-xorg/config/modules multiselect',
				'value' => 'i2c, bitmap, ddc, dri, extmod, freetype, glx, int10, type1, vbe',
				'type' => 'string'),


		);

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
		print "#\n";
		print "# X11 parameters\n";
		print "#\n";

		$this->DefaultPreseed('x11',$this->m_params);
	}	
	public function ScriptLate()
	{
		global $config;
		print "#\n";
		print "# X11 setup\n";
		print "#\n";

		return;
		
		$cursor_theme = $this->ReadString('x11','cursortheme','crystalwhite','string');

?>
cat > /usr/share/icons/default/index.theme <<EOF_CURSOR_THEME
[Icon theme] 
Inherits=<?php echo $cursor_theme; ?>

EOF_CURSOR_THEME

echo "Changed X11 mouse cursors"

<?php
		
	}
};

?>

