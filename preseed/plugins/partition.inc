<?php

class CPreseedPluginPartition extends CPreseedPluginBase
{
	private $m_params = array(

#
##### Partitions ######
#
#### WARNING: Be careful with these settings, they could easily destroy data on your disk

#d-i	partman-auto/init_automatically_partition	select Use the largest continuous free space
#d-i	partman-auto/choose_recipe	select All files in one partition (recommended for new users)
#d-i	partman-auto/choose_recipe	select Desktop machine
#d-i	partman-auto/choose_recipe	select Multi-user workstation
#d-i	partman-auto/expert_recipe_file	string /hd-media/recipe

#d-i	partman/confirm_write_new_label	boolean true
#d-i	partman/choose_partition	select Finish partitioning and write changes to disk
#d-i	partman/confirm			boolean	true

    
		'disk' => array('preseed' => 'd-i partman-auto/disk string',
				'value' => '/dev/discs/disc0/disc',
				'type' => 'string'),
		'method' => array('preseed' => 'd-i partman-auto/method string',
				'value' => 'regular',
				'type' => 'string'),

		'fatoptions' => array('preseed' => 'd-i partman-basicfilesystems/fatoptions multiselect',
				'value' => '',
				'type' => 'string')
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
		print "# Partition parameters\n";
		print "#\n";

		$this->DefaultPreseed('partition',$this->m_params);
	}	
};

?>

