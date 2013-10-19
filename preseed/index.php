<?php

header("Content-Type: text/plain");

echo "PHP calling";

$dir = opendir('./plugins');

while($name = readdir($dir))
{
	echo "Plugin $name\n";
}

?>

