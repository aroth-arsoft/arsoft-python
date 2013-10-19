<?php

class CPreseedPluginBase
{
	public function __construct($ldap_cxn,$client) 
	{
		$this->m_ldap = $ldap_cxn;
		$this->m_client = $client;
    	}

	public function Initialize()
	{
	}

	public function Deinitialize()
	{
	}	

	public function Preseed()
	{
	}
	public function ScriptEarly()
	{
	}
	public function ScriptLate()
	{
	}

	public function DefaultPreseed($section,$params)
	{
		while(list($name, $val) = each($params))
		{
			
			$val['value'] = $this->ReadString($section,$name, $val['value'], $val['type']);

			if(is_array($val['preseed']))
			{
				foreach($val['preseed'] as $tmp)
				{
					print "$tmp {$val['value']}\n";
				}
			}
			else
			{
				print "{$val['preseed']} {$val['value']}\n";
			}
		}
	}

	public function ReadString($section,$key,$default,$type)
	{
		global $config;

		$use_default = true;
		$value = '';
		foreach($this->m_client['class'] as $class)
		{
			$dn = "cn=$key,ou=$class,ou=$section,{$config['ldap']['base']}";

			$ret = $this->ReadEntry($dn,$value,$type);
			if($ret)
				$use_default = false;
		}
		if($use_default)
			$value = $default;
		if(is_array($value))
		{
			if($type == 'string-array')
				$value = implode(' ',$value);
			else if($type == 'multiselect')
				$value = implode(', ',$value);
		}
		return $value;
	}

	public function ReadEntry($dn,&$value,$type)
	{
		$entry = @$this->m_ldap->getEntry($dn);
        	if (Net_Ldap::isError($entry)) 
		{
			#print "# LDAP Error ". $entry->getMessage() . '\n';
			$ret = false;
        	} 
		else 
		{
			$ret = true;
			$newtype = $entry->getValue('preseedType');
			if (Net_Ldap::isError($newtype)) 
			{
				print "# LDAP Error ". $newtype->getMessage() . '\n';
				$ret = false;
			}

			$newvalue = $entry->getValue('preseedValue');
			if (Net_Ldap::isError($newvalue)) 
			{
				print "# LDAP Error ". $newvalue->getMessage() . '\n';
				$ret = false;
			}

			if($ret)
			{
				if($type == 'array' || $type == 'multiselect' || $type == 'string-array')
				{
					if(!is_array($value))
						$value = array();
					if(is_array($newvalue))
					{
						foreach($newvalue as $tmp)
						{
							array_push($value,$tmp);
						}
					}
					else
					{
						array_push($value,$newvalue);
					}
				}
				else
				{
					$value = $newvalue;
				}
			}
        }
		return $ret;
	}

	protected $m_ldap = NULL;
	protected $m_client = NULL;

};

?>
