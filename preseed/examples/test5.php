<?php

$user=$_GET['user'];
$passwd=$_GET['passwd'];

try
{
	$princ = new KRB5Ticket();
	$princ->initPassword( $user, $passwd);
	var_dump($princ);
}
catch (Exception $e) { 
	   echo 'Line: '.$e->getLine().'<br>'; 
	      echo 'File: '.$e->getFile().'<br>'; 
	      echo '<br>Trace: <br>'; 
		     echo '<pre>'; 
		     print_r($e->getTrace()); 
			    echo '</pre>'; 
} 
?>
